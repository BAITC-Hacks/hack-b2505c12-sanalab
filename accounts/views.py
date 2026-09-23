from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .models import AccountProfile


ROLE_NAMES = {
    AccountProfile.Role.BUSINESS: "представителя бизнеса",
    AccountProfile.Role.STUDENT: "студента",
}


def choose_role(request):
    return render(request, "accounts/choose_role.html")


def register_view(request, role):
    if request.user.is_authenticated:
        return redirect(
            "accounts:dashboard",
            role=request.user.account_profile.role,
        )

    form = UserCreationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            user = form.save()
            AccountProfile.objects.create(user=user, role=role)

        login(request, user)
        return redirect("accounts:dashboard", role=role)

    return render(request, "accounts/register.html", {
        "form": form,
        "role": role,
        "role_name": ROLE_NAMES[role],
    })


def login_view(request, role):
        if request.user.is_authenticated:
            return redirect(
                "accounts:dashboard",
                role=request.user.account_profile.role,
            )
        form = AuthenticationForm(request, data=request.POST or None)

        if request.method == "POST" and form.is_valid():
            user = form.get_user()
            profile = AccountProfile.objects.filter(user=user, role=role).first()

            if profile is None:
                form.add_error(None, "Неверные данные или тип аккаунта.")
            else:
                login(request, user)
                return redirect("accounts:dashboard", role=profile.role)

        return render(request, "accounts/login.html", {
            "form": form,
            "role": role,
            "role_name": ROLE_NAMES[role],
        })


@login_required(login_url="accounts:choose")
def dashboard_view(request, role):
    profile = AccountProfile.objects.filter(
        user=request.user,
    ).first()

    if profile is None or profile.role != role:
        raise PermissionDenied

    return render(
        request,
        "accounts/dashboard.html",
        {
            "role": profile.role,
            "role_name": ROLE_NAMES[profile.role],
        },
    )

@require_GET
def profile_view(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Необходимо войти в аккаунт."},
            status=401,
        )

    profile = AccountProfile.objects.filter(user=request.user).first()
    if profile is None:
        return JsonResponse(
            {"error": "Для пользователя не указан тип аккаунта."},
            status=403,
        )

    return JsonResponse({
        "username": request.user.get_username(),
        "role": profile.role,
        "role_display": profile.get_role_display(),
    })