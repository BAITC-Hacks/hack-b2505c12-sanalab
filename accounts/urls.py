from django.contrib.auth.views import LogoutView
from django.urls import path, register_converter

from . import views


class RoleConverter:
    regex = "business|student"

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


register_converter(RoleConverter, "role")

app_name = "accounts"

urlpatterns = [
    path("", views.choose_role, name="choose"),
    path("<role:role>/register/", views.register_view, name="register"),
    path("<role:role>/login/", views.login_view, name="login"),
    path("<role:role>/", views.dashboard_view, name="dashboard"),
    path("logout/", LogoutView.as_view(next_page="accounts:choose"), name="logout"),
    path("profile/", views.profile_view, name="profile"),
]