"""Example views for the blog API shown in docs/quickstart.md."""

from __future__ import annotations

from rest_framework import viewsets
from rest_framework.serializers import BaseSerializer

from examples.blog.exceptions import ArticleAlreadyPublishedError
from examples.blog.models import Article
from examples.blog.serializers import ArticleSerializer


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.select_related("author").all()
    serializer_class = ArticleSerializer

    def perform_update(self, serializer: BaseSerializer[Article]) -> None:
        instance = serializer.instance
        if isinstance(instance, Article) and instance.published:
            raise ArticleAlreadyPublishedError(extensions={"article_id": instance.id})
        serializer.save()
