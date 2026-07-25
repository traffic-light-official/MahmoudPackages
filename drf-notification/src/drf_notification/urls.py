"""Ready-to-include URL configuration for the notification preference center.

Usage:
    .. code-block:: python

        # urls.py
        from django.urls import include, path

        urlpatterns = [
            path("notifications/", include("drf_notification.urls")),
        ]
"""

from __future__ import annotations

from django.urls import path
from rest_framework.routers import DefaultRouter

from drf_notification.views import (
    NotificationPreferenceViewSet,
    NotificationSettingsView,
    NotificationViewSet,
    PreferenceCenterView,
    UnsubscribeView,
    WebhookTargetViewSet,
)

app_name = "drf_notification"

router = DefaultRouter()
router.register("items", NotificationViewSet, basename="notification")
router.register("preferences", NotificationPreferenceViewSet, basename="notification-preference")
router.register("webhook-targets", WebhookTargetViewSet, basename="webhook-target")

urlpatterns = [
    *router.urls,
    path("settings/", NotificationSettingsView.as_view(), name="notification-settings"),
    path("unsubscribe/<str:token>/", UnsubscribeView.as_view(), name="notification-unsubscribe"),
    path(
        "preference-center/<str:token>/",
        PreferenceCenterView.as_view(),
        name="notification-preference-center",
    ),
]
