"""Views demonstrating this package's main features."""

from __future__ import annotations

from typing import Any

from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from drf_async import AsyncAPIView, AsyncModelViewSet, AsyncSimpleRateThrottle, BaseAsyncPermission
from examples.blog.models import Article
from examples.blog.serializers import ArticleSerializer


class PingView(AsyncAPIView):
    """The simplest possible async view: no database access at all."""

    permission_classes = [AllowAny]

    async def get(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        return Response({"pong": True})


class AllowRegisteredClients(BaseAsyncPermission):
    """An async-native permission - pretend this calls an external auth service."""

    message = "Unknown client."

    async def has_permission(self, request: Any, view: Any) -> bool:
        return request.headers.get("X-Client-Id") == "trusted-client"


class OncePerMinuteThrottle(AsyncSimpleRateThrottle):
    """An async-native throttle: one request per client per minute."""

    scope = "example_once_per_minute"
    THROTTLE_RATES = {"example_once_per_minute": "1/min"}

    def get_cache_key(self, request: Any, view: Any) -> str:
        ident = request.headers.get("X-Client-Id", "anonymous")
        return self.cache_format % {"scope": self.scope, "ident": ident}


class ArticleViewSet(AsyncModelViewSet):
    """Full async CRUD over :class:`~examples.blog.models.Article`."""

    permission_classes = [AllowAny]
    serializer_class = ArticleSerializer
    queryset = Article.objects.select_related("author").all()
