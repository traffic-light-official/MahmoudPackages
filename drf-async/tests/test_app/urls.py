"""URLconf for the test app."""

from __future__ import annotations

from django.urls import path
from rest_framework.routers import DefaultRouter

from tests.test_app.views import (
    ArticleViewSet,
    AsyncPermissionAllowedView,
    AsyncPermissionDeniedView,
    PingView,
    SyncPermissionView,
    ThrottledView,
)

router = DefaultRouter()
router.register("articles", ArticleViewSet, basename="article")

urlpatterns = [
    path("ping/", PingView.as_view()),
    path("sync-permission/", SyncPermissionView.as_view()),
    path("async-permission-denied/", AsyncPermissionDeniedView.as_view()),
    path("async-permission-allowed/", AsyncPermissionAllowedView.as_view()),
    path("throttled/", ThrottledView.as_view()),
    *router.urls,
]
