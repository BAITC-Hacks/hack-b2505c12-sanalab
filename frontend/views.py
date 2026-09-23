import secrets

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import BusinessRequestForm, ProposalForm
from backend.models import BusinessRequest

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from accounts.models import AccountProfile
from .models import Proposal

OWNER_SESSION_KEY = "business_request_owner"


def index(request):
    tasks = BusinessRequest.objects.none()
    applied_task_ids = set()

    if request.user.is_authenticated:
        is_student = AccountProfile.objects.filter(
            user=request.user,
            role=AccountProfile.Role.STUDENT,
        ).exists()

        if is_student:
            tasks = BusinessRequest.objects.filter(
                status=BusinessRequest.Status.CONFIRMED,
            ).order_by("-confirmed_at", "-pk")

            applied_task_ids = set(
                Proposal.objects.filter(student=request.user)
                .values_list("task_id", flat=True)
            )

    return render(request, "frontend/index.html", {
        "title": "Добро пожаловать!",
        "tasks": tasks,
        "applied_task_ids": applied_task_ids,
    })


@csrf_protect
@require_POST
@login_required(login_url="accounts:choose")
def submit_proposal(request, pk):
    is_student = AccountProfile.objects.filter(
        user=request.user,
        role=AccountProfile.Role.STUDENT,
    ).exists()
    if not is_student:
        raise PermissionDenied

    task = get_object_or_404(
        BusinessRequest,
        pk=pk,
        status=BusinessRequest.Status.CONFIRMED,
    )

    form = ProposalForm(request.POST)
    if not form.is_valid():
        messages.error(
            request,
            "Опишите предложение: от 10 до 5000 символов.",
        )
        return redirect("frontend:home")

    proposal, created = Proposal.objects.get_or_create(
        task=task,
        student=request.user,
        defaults={"solution": form.cleaned_data["solution"]},
    )

    if created:
        messages.success(request, "Предложение отправлено.")
    else:
        messages.info(request, "Вы уже подали заявку на эту задачу.")

    return redirect("frontend:home")


def _owned_requests(request):
    """Нет ключа сессии — нет доступа к чужим или старым карточкам."""
    key = request.session.get(OWNER_SESSION_KEY)
    if not isinstance(key, str) or len(key) != 64:
        return BusinessRequest.objects.none()
    return BusinessRequest.objects.filter(owner_key=key)


def _owner_key(request):
    key = request.session.get(OWNER_SESSION_KEY)
    if not isinstance(key, str) or len(key) != 64:
        key = secrets.token_hex(32)
        request.session[OWNER_SESSION_KEY] = key
    return key


def _posted_revision(request):
    try:
        return int(request.POST.get("revision", ""))
    except (TypeError, ValueError):
        return None


def _render_request_form(request, form, item=None, *, status=200):
    version = item.revision if item is not None else ""
    # При конфликте НЕ подменяем старую версию новой за спиной пользователя.
    # Сначала нужно открыть актуальную карточку и снова нажать «Редактировать».
    if item is not None and request.method == "POST":
        version = request.POST.get("revision", "")
    return render(request, "frontend/business_request.html", {
        "form": form,
        "item": item,
        "is_edit": item is not None,
        "form_revision": version,
    }, status=status)


@never_cache
@csrf_protect
@require_http_methods(["GET", "POST"])
def business_request(request):
    form = BusinessRequestForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.owner_key = _owner_key(request)
        item.status = BusinessRequest.Status.DRAFT
        item.confirmed_at = None
        item.save()
        messages.success(request, "Черновик сохранён. Проверьте карточку перед подтверждением.")
        return redirect("frontend:request_detail", pk=item.pk)
    return _render_request_form(request, form)


@never_cache
@require_GET
def request_list(request):
    page_obj = Paginator(_owned_requests(request), 10).get_page(request.GET.get("page"))
    return render(request, "frontend/request_list.html", {"page_obj": page_obj})


@never_cache
@require_GET
def request_detail(request, pk):
    item = get_object_or_404(_owned_requests(request), pk=pk)
    return render(request, "frontend/request_detail.html", {"item": item})


@never_cache
@csrf_protect
@require_http_methods(["GET", "POST"])
def request_edit(request, pk):
    item = get_object_or_404(_owned_requests(request), pk=pk)
    # instance заполняет форму текущими значениями, а не пустыми полями.
    form = BusinessRequestForm(
        request.POST if request.method == "POST" else None,
        instance=item,
    )
    if request.method == "POST" and form.is_valid():
        version = _posted_revision(request)
        if version == item.revision:
            # Условное обновление той же записи защищает от сохранения устаревшей
            # вкладки. Не создаём новую карточку и не перезаписываем чужие правки.
            updated = _owned_requests(request).filter(
                pk=pk, revision=version,
            ).update(
                **{name: form.cleaned_data[name] for name in BusinessRequestForm.Meta.fields},
                status=BusinessRequest.Status.DRAFT,
                confirmed_at=None,
                updated_at=timezone.now(),
                revision=F("revision") + 1,
            )
            if updated:
                messages.success(
                    request,
                    "Изменения сохранены. Обновлённую карточку нужно подтвердить вручную.",
                )
                return redirect("frontend:request_detail", pk=pk)
        form.add_error(None, (
            "Карточка уже изменилась в другой вкладке или устарела версия формы. "
            "Откройте актуальную карточку и снова нажмите «Редактировать». "
            "Ваш введённый текст остался ниже; перед переходом его можно скопировать."
        ))
        return _render_request_form(request, form, item, status=409)
    return _render_request_form(request, form, item)


@never_cache
@csrf_protect
@require_POST
def request_confirm(request, pk):
    item = get_object_or_404(_owned_requests(request), pk=pk)
    # Проверяем явное действие на сервере, а не только HTML required.
    if request.POST.get("confirm") != "yes":
        messages.error(request, "Отметьте, что вы проверили данные карточки.")
        return redirect("frontend:request_detail", pk=pk)

    if item.status == BusinessRequest.Status.CONFIRMED:
        messages.info(request, "Эта карточка уже подтверждена.")
        return redirect("frontend:request_detail", pk=pk)

    version = _posted_revision(request)
    if version != item.revision:
        messages.error(request, "Карточка изменилась. Проверьте актуальные данные и подтвердите ещё раз.")
        return redirect("frontend:request_detail", pk=pk)

    # Нельзя подтвердить неполную старую запись или обойти проверку формы.
    check_form = BusinessRequestForm(
        {name: getattr(item, name) for name in BusinessRequestForm.Meta.fields},
        instance=item,
    )
    if not check_form.is_valid():
        messages.error(request, "Перед подтверждением заполните все шесть полей корректно.")
        return redirect("frontend:request_edit", pk=pk)

    now = timezone.now()
    updated = _owned_requests(request).filter(
        pk=pk, revision=version, status=BusinessRequest.Status.DRAFT,
    ).update(
        status=BusinessRequest.Status.CONFIRMED,
        confirmed_at=now,
        updated_at=now,
        revision=F("revision") + 1,
    )
    if updated:
        messages.success(request, "Заявка подтверждена вручную.")
    else:
        messages.error(request, "Карточка уже изменилась. Проверьте её текущий статус.")
    return redirect("frontend:request_detail", pk=pk)

