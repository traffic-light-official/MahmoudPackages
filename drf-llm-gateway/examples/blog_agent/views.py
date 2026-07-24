"""Example views for the blog agent backend shown in docs/examples.md."""

from __future__ import annotations

from rest_framework import viewsets

from drf_llm_gateway import expose_as_tool
from examples.blog_agent.models import Article
from examples.blog_agent.serializers import ArticleSerializer


@expose_as_tool(
    actions=["list", "retrieve", "create", "partial_update"],
    examples={"create": [{"title": "My First Post", "body": "Hello!", "author": 1}]},
)
class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
