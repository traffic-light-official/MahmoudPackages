"""Views used by the integration test suite to exercise every handler path."""

from __future__ import annotations

from django.http import Http404
from rest_framework import viewsets
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from drf_error_response_standardizer.exceptions import ConflictError
from tests.test_app.models import Article
from tests.test_app.serializers import ArticleSerializer


class ArticleViewSet(viewsets.ModelViewSet):
    """A standard ``ModelViewSet`` used to exercise nested validation errors."""

    queryset = Article.objects.select_related("author").all()
    serializer_class = ArticleSerializer


class RaiseValueErrorView(APIView):
    """Raises a plain, non-DRF exception to exercise the catch-all 500 path."""

    def get(self, request: Request) -> Response:
        raise ValueError("Something went wrong internally.")


class RaiseConflictView(APIView):
    """Raises :class:`~drf_error_response_standardizer.exceptions.ConflictError`."""

    def get(self, request: Request) -> Response:
        raise ConflictError("Order has already shipped.", extensions={"order_id": 42})


class RaiseHttp404View(APIView):
    """Raises Django's :class:`~django.http.Http404` directly (not DRF's ``NotFound``)."""

    def get(self, request: Request) -> Response:
        raise Http404("Widget not found.")


class RequiresAuthView(APIView):
    """Requires authentication so unauthenticated requests raise ``NotAuthenticated``.

    Uses :class:`~rest_framework.authentication.BasicAuthentication` so DRF
    sets ``exc.auth_header``, letting the test suite verify the handler
    preserves the ``WWW-Authenticate`` response header.
    """

    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response({"ok": True})


class BurstRateThrottle(UserRateThrottle):
    """A deliberately tiny throttle rate so tests can trigger ``Throttled``."""

    scope = "burst"


class ThrottledView(APIView):
    """A view throttled after a single request, to exercise the ``Retry-After`` header."""

    throttle_classes = [BurstRateThrottle]

    def get(self, request: Request) -> Response:
        return Response({"ok": True})
