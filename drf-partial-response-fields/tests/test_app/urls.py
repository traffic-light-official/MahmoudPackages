"""URL configuration for the test suite's Django project."""

from __future__ import annotations

from django.urls import path
from rest_framework.routers import DefaultRouter

from tests.test_app.views import ArticlePKAuthorListView, ArticleViewSet

router = DefaultRouter()
router.register("articles", ArticleViewSet, basename="article")

urlpatterns = [
    *router.urls,
    path("articles-pk-author/", ArticlePKAuthorListView.as_view(), name="article-pk-author-list"),
]
