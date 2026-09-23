from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import BusinessRequestForm


@require_http_methods(["GET", "POST"])
def business_request(request):
    form = BusinessRequestForm(
        request.POST if request.method == "POST" else None
    )

    if request.method == "POST" and form.is_valid():
        form.save()

        messages.success(
            request,
            "Заявка сохранена! Спасибо за описание задачи.",
        )
        return redirect("frontend:business_request")

    return render(
        request,
        "frontend/business_request.html",
        {"form": form},
    )

def index(request):
    return render(
        request,
        "frontend/index.html",
        {"title": "Добро пожаловать!"},
    )