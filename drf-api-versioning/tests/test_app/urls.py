"""URLconf for the test app - one route per versioning scheme."""

from __future__ import annotations

from django.urls import include, path, re_path

from tests.test_app.views import (
    AcceptHeaderPingView,
    HostNamePingView,
    NamespacePingView,
    QueryParameterPingView,
    URLPathPingView,
)

_namespace_patterns = ([path("ping/", NamespacePingView.as_view(), name="ping")], "test_app")

urlpatterns = [
    re_path(r"^(?P<version>[^/]+)/url-ping/$", URLPathPingView.as_view()),
    path("accept-ping/", AcceptHeaderPingView.as_view()),
    path("query-ping/", QueryParameterPingView.as_view()),
    path("host-ping/", HostNamePingView.as_view()),
    path("plain-ns-ping/", NamespacePingView.as_view()),
    path("v1/ns-ping/", include(_namespace_patterns, namespace="v1")),
    path("v2/ns-ping/", include(_namespace_patterns, namespace="v2")),
    path("v3/ns-ping/", include(_namespace_patterns, namespace="v3")),
    path("v9/ns-ping/", include(_namespace_patterns, namespace="v9")),
]
