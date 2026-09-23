from django.urls import path
from . import views

app_name = "frontend"

urlpatterns = [
    path("", views.index, name="home"),
    path("request/", views.business_request, name="business_request"),
    path("requests/", views.request_list, name="request_list"),
    path("request/<int:pk>/", views.request_detail, name="request_detail"),
    path("request/<int:pk>/edit/", views.request_edit, name="request_edit"),
    path("request/<int:pk>/confirm/", views.request_confirm, name="request_confirm"),
    path(
    "request/<int:pk>/propose/",
    views.submit_proposal,
    name="submit_proposal",
),
]
