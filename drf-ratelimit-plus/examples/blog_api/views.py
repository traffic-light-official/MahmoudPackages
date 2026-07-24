"""Example view for the tiered blog API shown in docs/examples.md."""

from __future__ import annotations

from rest_framework import viewsets

from drf_ratelimit_plus import RateLimitHeadersMixin, rate_limit
from examples.blog_api.models import Article
from examples.blog_api.serializers import ArticleSerializer


class ArticleViewSet(RateLimitHeadersMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    throttle_classes = [
        rate_limit(
            rate={"free": "60/h", "pro": "1000/h"},
            algorithm="token_bucket",
            burst=10,
            key="user",
        ),
    ]
