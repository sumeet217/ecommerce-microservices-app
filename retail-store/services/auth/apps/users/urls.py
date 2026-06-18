"""Auth Service — Users App URL Configuration"""

from django.urls import path

from .views import (
    CustomTokenRefreshView,
    CustomTokenVerifyView,
    LoginView,
    LogoutView,
    MeView,
    RegisterView,
)

app_name = "users"

urlpatterns = [
    # ── Authentication ────────────────────────────────────────────────────────
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", CustomTokenRefreshView.as_view(), name="token-refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("verify/", CustomTokenVerifyView.as_view(), name="token-verify"),
    # ── User Profile ──────────────────────────────────────────────────────────
    path("me/", MeView.as_view(), name="me"),
]
