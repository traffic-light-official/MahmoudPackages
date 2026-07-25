"""Ready-to-include URL configuration for the authentication API.

Usage:
    .. code-block:: python

        # urls.py
        from django.urls import include, path

        urlpatterns = [
            path("auth/", include("drf_jwt_auth_kit.urls")),
        ]
"""

from __future__ import annotations

from django.urls import path
from rest_framework.routers import DefaultRouter

from drf_jwt_auth_kit.views import (
    DeviceViewSet,
    LoginHistoryViewSet,
    LoginView,
    LogoutAllView,
    LogoutView,
    RefreshView,
    TOTPConfirmView,
    TOTPDisableView,
    TOTPSetupView,
)

app_name = "drf_jwt_auth_kit"

router = DefaultRouter()
router.register("devices", DeviceViewSet, basename="device")
router.register("login-history", LoginHistoryViewSet, basename="login-history")

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", RefreshView.as_view(), name="refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("logout-all/", LogoutAllView.as_view(), name="logout-all"),
    path("mfa/totp/setup/", TOTPSetupView.as_view(), name="totp-setup"),
    path("mfa/totp/confirm/", TOTPConfirmView.as_view(), name="totp-confirm"),
    path("mfa/totp/disable/", TOTPDisableView.as_view(), name="totp-disable"),
    *router.urls,
]
