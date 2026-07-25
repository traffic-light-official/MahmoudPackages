"""Views for the test app, one per registry-aware versioning scheme."""

from __future__ import annotations

from rest_framework.response import Response
from rest_framework.views import APIView

from drf_api_versioning.mixins import DeprecationHeaderMixin
from drf_api_versioning.versioning import (
    AcceptHeaderVersioning,
    HostNameVersioning,
    NamespaceVersioning,
    QueryParameterVersioning,
    URLPathVersioning,
)


class _PingView(DeprecationHeaderMixin, APIView):
    def get(self, request: object, *args: object, **kwargs: object) -> Response:
        return Response({"version": request.version})  # type: ignore[attr-defined]


class URLPathPingView(_PingView):
    versioning_class = URLPathVersioning


class NamespacePingView(_PingView):
    versioning_class = NamespaceVersioning


class AcceptHeaderPingView(_PingView):
    versioning_class = AcceptHeaderVersioning


class QueryParameterPingView(_PingView):
    versioning_class = QueryParameterVersioning


class HostNamePingView(_PingView):
    versioning_class = HostNameVersioning
