"""URLconf used by the test suite."""

from __future__ import annotations

from rest_framework.routers import DefaultRouter

from tests.test_app.views import ArticleViewSet, AuthorViewSet

router = DefaultRouter()
router.register("authors", AuthorViewSet)
router.register("articles", ArticleViewSet)

urlpatterns = router.urls
