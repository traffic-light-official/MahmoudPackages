"""Views for the test app, covering every feature this package adds."""

from __future__ import annotations

from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet

from drf_serializer_performance_profiler import ProfileSerializerViewMixin
from tests.test_app.models import Article
from tests.test_app.serializers import ArticleSerializer


class ArticleViewSet(ProfileSerializerViewMixin, ModelViewSet):
    """Full CRUD over :class:`~tests.test_app.models.Article`, with profiling enabled."""

    permission_classes = [AllowAny]
    serializer_class = ArticleSerializer
    queryset = Article.objects.select_related("author").all()
