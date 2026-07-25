"""Views for the test app, covering every feature this package adds."""

from __future__ import annotations

from typing import Any

from django.http import HttpRequest, JsonResponse
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from drf_permission_debugger import PermissionDebugMixin
from tests.test_app.models import Article
from tests.test_app.permissions import DenyAll, IsOwner, Undocumented
from tests.test_app.serializers import ArticleSerializer


class PingView(PermissionDebugMixin, APIView):
    """Guarded by a single, always-granting permission."""

    permission_classes = [AllowAny]

    def get(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        return Response({"pong": True})


class MultiPermissionDeniedView(PermissionDebugMixin, APIView):
    """Guarded by two permissions - the first grants, the second denies."""

    permission_classes = [IsAuthenticated, DenyAll]

    def get(self, request: Any, *args: Any, **kwargs: Any) -> Response:  # pragma: no cover
        return Response({"should": "never reach here"})


class ArticleViewSet(PermissionDebugMixin, ModelViewSet):
    """Guarded by an object-level permission, for retrieve/update/destroy checks."""

    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = ArticleSerializer
    queryset = Article.objects.select_related("owner").all()


class NoPermissionsView(APIView):
    """No permission/authentication classes configured at all, plus one throttle."""

    permission_classes: list[type] = []
    authentication_classes: list[type] = []
    throttle_classes = [AnonRateThrottle]

    def get(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        return Response({"ok": True})


class UndocumentedPermissionView(APIView):
    """Guarded by a permission class with no docstring of its own."""

    permission_classes = [Undocumented]

    def get(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        return Response({"ok": True})


def plain_function_view(request: HttpRequest) -> JsonResponse:
    """A truly plain Django function-based view - has no ``.cls``/``.view_class`` to introspect."""
    return JsonResponse({"ok": True})
