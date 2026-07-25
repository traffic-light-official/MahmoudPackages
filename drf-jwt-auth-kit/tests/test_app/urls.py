"""URL configuration for the test suite's Django project."""

from __future__ import annotations

from django.urls import include, path

urlpatterns = [
    path("auth/", include("drf_jwt_auth_kit.urls")),
]
