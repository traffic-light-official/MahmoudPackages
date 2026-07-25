"""Example views for the blog API shown in docs/quickstart.md."""

from __future__ import annotations

from rest_framework import viewsets

from drf_notification.notify import notify
from examples.blog.models import Article
from examples.blog.serializers import ArticleSerializer


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.select_related("author").all()
    serializer_class = ArticleSerializer

    def perform_create(self, serializer: ArticleSerializer) -> None:
        article: Article = serializer.save()
        for subscriber in article.author.subscribers.all():
            notify(
                recipient=subscriber,
                event_key="article.published",
                context={"title": article.title, "url": article.get_absolute_url()},
            )
