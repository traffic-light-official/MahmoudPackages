"""URL configuration for the test suite's Django project."""

from __future__ import annotations

from django.urls import path
from rest_framework.routers import DefaultRouter

from tests.test_app.views import (
    ArticleViewSet,
    RaiseConflictView,
    RaiseHttp404View,
    RaiseValueErrorView,
    RequiresAuthView,
    ThrottledView,
)

router = DefaultRouter()
router.register("articles", ArticleViewSet, basename="article")

urlpatterns = [
    *router.urls,
    path("raise-value-error/", RaiseValueErrorView.as_view(), name="raise-value-error"),
    path("raise-conflict/", RaiseConflictView.as_view(), name="raise-conflict"),
    path("raise-404/", RaiseHttp404View.as_view(), name="raise-404"),
    path("requires-auth/", RequiresAuthView.as_view(), name="requires-auth"),
    path("throttled/", ThrottledView.as_view(), name="throttled"),
]
