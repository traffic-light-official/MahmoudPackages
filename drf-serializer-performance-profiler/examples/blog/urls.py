"""URL conf for the runnable example."""

from __future__ import annotations

from rest_framework.routers import DefaultRouter

from examples.blog.views import ArticleViewSet, OptimizedArticleViewSet

router = DefaultRouter()
router.register("articles", ArticleViewSet, basename="article")
router.register("optimized-articles", OptimizedArticleViewSet, basename="optimized-article")

urlpatterns = router.urls
