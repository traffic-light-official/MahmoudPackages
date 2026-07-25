"""URL configuration for the test suite's Django project."""

from __future__ import annotations

from django.urls import include, path

urlpatterns = [
    path("notifications/", include("drf_notification.urls")),
]
