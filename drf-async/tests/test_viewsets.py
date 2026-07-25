"""Tests for :mod:`drf_async.viewsets`."""

from __future__ import annotations

from typing import Any

from asgiref.sync import iscoroutinefunction
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from drf_async.viewsets import AsyncGenericViewSet
from tests.test_app.models import Article
from tests.test_app.serializers import ArticleSerializer


class _MixedViewSet(AsyncGenericViewSet):
    permission_classes = [AllowAny]
    serializer_class = ArticleSerializer
    queryset = Article.objects.all()

    async def async_action(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        return Response({"ok": True})

    def sync_action(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        return Response({"ok": True})


class TestAsyncGenericViewSetAsView:
    def test_marks_view_async_when_every_bound_action_is_a_coroutine(self) -> None:
        view = _MixedViewSet.as_view({"get": "async_action"})
        assert iscoroutinefunction(view) is True

    def test_does_not_mark_view_async_when_any_bound_action_is_sync(self) -> None:
        view = _MixedViewSet.as_view({"get": "sync_action"})
        assert iscoroutinefunction(view) is False
