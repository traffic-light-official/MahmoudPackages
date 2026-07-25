"""Views for the test app, covering every feature this package adds."""

from __future__ import annotations

from typing import Any

from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from drf_async import (
    AsyncAPIView,
    AsyncModelViewSet,
    AsyncSimpleRateThrottle,
    BaseAsyncPermission,
)
from tests.test_app.models import Article
from tests.test_app.serializers import ArticleSerializer


class PingView(AsyncAPIView):
    """A trivial async view: no I/O, just proves ``async def get`` works at all."""

    permission_classes: list[type] = [AllowAny]

    async def get(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        return Response({"pong": True})


class SyncPermissionView(AsyncAPIView):
    """Guarded by a classic, synchronous DRF permission class."""

    permission_classes = [IsAuthenticated]

    async def get(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        return Response({"authenticated": True})


class DenyAllAsyncPermission(BaseAsyncPermission):
    """An async-native permission that always denies."""

    message = "Denied by DenyAllAsyncPermission."

    async def has_permission(self, request: Any, view: Any) -> bool:
        return False


class AllowAllAsyncPermission(BaseAsyncPermission):
    """An async-native permission that always allows."""

    async def has_permission(self, request: Any, view: Any) -> bool:
        return True


class AsyncPermissionDeniedView(AsyncAPIView):
    """Guarded by a genuinely async permission class that denies.

    ``authentication_classes = []`` so ``APIView.permission_denied()``
    doesn't mask our permission's own message with a generic
    "Authentication credentials were not provided." - DRF's
    ``permission_denied()`` prefers ``NotAuthenticated`` over the
    denying permission's ``message`` whenever *any* authenticator is
    configured but none succeeded, regardless of which permission
    actually denied the request.
    """

    permission_classes = [DenyAllAsyncPermission]
    authentication_classes: list[type] = []

    async def get(self, request: Any, *args: Any, **kwargs: Any) -> Response:  # pragma: no cover
        return Response({"should": "never reach here"})


class AsyncPermissionAllowedView(AsyncAPIView):
    """Guarded by a genuinely async permission class that allows."""

    permission_classes = [AllowAllAsyncPermission]

    async def get(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        return Response({"allowed": True})


class OneRequestPerMinuteThrottle(AsyncSimpleRateThrottle):
    """An async-native throttle allowing exactly one request per client per minute.

    Keys on the ``X-Client-Id`` header if present, falling back to
    ``get_ident()`` (client IP) otherwise - the header makes "two
    different clients" trivial to simulate in tests without depending
    on how a given test client maps to a request's client IP.
    """

    scope = "test_one_per_minute"
    THROTTLE_RATES = {"test_one_per_minute": "1/min"}

    def get_cache_key(self, request: Any, view: Any) -> str:
        ident = request.META.get("HTTP_X_CLIENT_ID") or self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


class ThrottledView(AsyncAPIView):
    """Guarded by an async-native throttle allowing one request per minute."""

    permission_classes = [AllowAny]
    throttle_classes = [OneRequestPerMinuteThrottle]

    async def get(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        return Response({"ok": True})


class _TwoPerPagePagination(PageNumberPagination):
    page_size = 2


class ArticleViewSet(AsyncModelViewSet):
    """Full async CRUD + pagination over :class:`~tests.test_app.models.Article`."""

    permission_classes = [AllowAny]
    serializer_class = ArticleSerializer
    queryset = Article.objects.select_related("author").all()
    pagination_class = _TwoPerPagePagination
