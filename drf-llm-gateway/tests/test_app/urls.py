"""URL configuration for the test suite's Django project."""

from __future__ import annotations

from rest_framework.routers import DefaultRouter

from tests.test_app.views import ArticleViewSet, PublicArticleViewSet

router = DefaultRouter()
router.register("articles", ArticleViewSet, basename="article")
router.register("public-articles", PublicArticleViewSet, basename="public-article")

urlpatterns = [*router.urls]
