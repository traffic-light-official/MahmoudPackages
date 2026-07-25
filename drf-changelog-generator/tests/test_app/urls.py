"""URL configuration for the test suite's Django project."""

from __future__ import annotations

from rest_framework.routers import DefaultRouter

from tests.test_app.views import ArticleViewSet

router = DefaultRouter()
router.register("articles", ArticleViewSet, basename="article")

urlpatterns = [*router.urls]
