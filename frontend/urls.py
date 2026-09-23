from django.urls import path
from . import views

app_name = "frontend"

urlpatterns = [
    path("", views.index, name="home"),
    path("request/", views.business_request, name="business_request"),
]
