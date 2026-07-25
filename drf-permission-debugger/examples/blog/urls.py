"""URL conf for the runnable example."""

from __future__ import annotations

from rest_framework.routers import DefaultRouter

from examples.blog.views import ArticleViewSet

router = DefaultRouter()
router.register("articles", ArticleViewSet, basename="article")

urlpatterns = router.urls
