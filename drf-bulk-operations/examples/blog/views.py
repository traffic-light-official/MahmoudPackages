"""Views demonstrating this package's main features."""

from __future__ import annotations

from rest_framework.permissions import AllowAny

from drf_bulk_operations import BulkModelViewSet
from examples.blog.models import Article
from examples.blog.serializers import ArticleSerializer


class ArticleViewSet(BulkModelViewSet):
    """Full bulk create/update/destroy over :class:`~examples.blog.models.Article`."""

    permission_classes = [AllowAny]
    serializer_class = ArticleSerializer
    queryset = Article.objects.select_related("author").all()
