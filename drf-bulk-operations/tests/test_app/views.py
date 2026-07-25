"""Views for the test app, covering every feature this package adds."""

from __future__ import annotations

from rest_framework.permissions import AllowAny

from drf_bulk_operations import BulkModelViewSet
from tests.test_app.models import Article
from tests.test_app.serializers import ArticleSerializer


class ArticleViewSet(BulkModelViewSet):
    """Full bulk create/update/destroy over :class:`~tests.test_app.models.Article`."""

    permission_classes = [AllowAny]
    serializer_class = ArticleSerializer
    queryset = Article.objects.select_related("author").all()
