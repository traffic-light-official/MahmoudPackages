"""URL conf for the test app."""

from __future__ import annotations

from django.urls import path
from rest_framework.routers import DefaultRouter

from tests.test_app.views import (
    ArticleViewSet,
    MultiPermissionDeniedView,
    NoPermissionsView,
    PingView,
    UndocumentedPermissionView,
    plain_function_view,
)

router = DefaultRouter()
router.register("articles", ArticleViewSet, basename="article")

urlpatterns = [
    path("ping/", PingView.as_view()),
    path("multi-denied/", MultiPermissionDeniedView.as_view()),
    path("no-permissions/", NoPermissionsView.as_view()),
    path("undocumented-permission/", UndocumentedPermissionView.as_view()),
    path("function-view/", plain_function_view),
    *router.urls,
]
