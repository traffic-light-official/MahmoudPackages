"""Views used by the test suite."""

from __future__ import annotations

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_llm_gateway import expose_as_tool
from tests.test_app.models import Article
from tests.test_app.serializers import ArticleSerializer


@expose_as_tool(
    actions=["list", "retrieve", "create", "update", "partial_update", "destroy", "publish"],
    examples={"create": [{"title": "Hello", "author": 1}]},
)
class ArticleViewSet(viewsets.ModelViewSet):
    """Manage blog articles."""

    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["post"])
    def publish(self, request: object, pk: int | None = None) -> Response:
        article = self.get_object()
        article.status = Article.Status.PUBLISHED
        article.save(update_fields=["status"])
        return Response(self.get_serializer(article).data)


@expose_as_tool(actions=["list", "retrieve"], name_prefix="public_article")
class PublicArticleViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only, unauthenticated access to published articles."""

    queryset = Article.objects.filter(status=Article.Status.PUBLISHED)
    serializer_class = ArticleSerializer
    permission_classes = []
