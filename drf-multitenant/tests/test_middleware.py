"""Tests for drf_multitenant.middleware.TenantMiddleware."""

from __future__ import annotations

import json
from collections.abc import Callable

import pytest
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory, override_settings

from drf_multitenant.context import get_current_tenant
from drf_multitenant.middleware import TenantMiddleware
from tests.test_app.models import Tenant

pytestmark = pytest.mark.django_db


def _make_middleware(
    inner: Callable[[HttpRequest], HttpResponse] | None = None,
) -> TenantMiddleware:
    def get_response(request: HttpRequest) -> HttpResponse:
        if inner is not None:
            return inner(request)
        return HttpResponse("ok")

    return TenantMiddleware(get_response)


class TestResolution:
    def test_binds_resolved_tenant_for_the_request(self, tenant_a: Tenant) -> None:
        observed = {}

        def inner(request: HttpRequest) -> HttpResponse:
            observed["tenant"] = get_current_tenant()
            return HttpResponse("ok")

        middleware = _make_middleware(inner)
        request = RequestFactory().get("/", HTTP_X_TENANT_ID=str(tenant_a.pk))
        response = middleware(request)

        assert response.status_code == 200
        assert observed["tenant"] == tenant_a

    def test_attaches_tenant_to_request(self, tenant_a: Tenant) -> None:
        middleware = _make_middleware()
        request = RequestFactory().get("/", HTTP_X_TENANT_ID=str(tenant_a.pk))
        middleware(request)
        assert request.tenant == tenant_a  # type: ignore[attr-defined]

    def test_resets_context_after_response(self, tenant_a: Tenant) -> None:
        middleware = _make_middleware()
        request = RequestFactory().get("/", HTTP_X_TENANT_ID=str(tenant_a.pk))
        middleware(request)
        assert get_current_tenant() is None

    def test_resets_context_even_if_view_raises(self, tenant_a: Tenant) -> None:
        def inner(request: HttpRequest) -> HttpResponse:
            raise ValueError("boom")

        middleware = _make_middleware(inner)
        request = RequestFactory().get("/", HTTP_X_TENANT_ID=str(tenant_a.pk))
        with pytest.raises(ValueError, match="boom"):
            middleware(request)
        assert get_current_tenant() is None


class TestStrictMode:
    def test_rejects_request_with_no_resolvable_tenant_by_default(self) -> None:
        middleware = _make_middleware()
        request = RequestFactory().get("/")
        response = middleware(request)
        assert response.status_code == 400
        assert "detail" in json.loads(response.content)

    def test_view_never_runs_when_rejected(self) -> None:
        called = {"value": False}

        def inner(request: HttpRequest) -> HttpResponse:
            called["value"] = True
            return HttpResponse("ok")

        middleware = _make_middleware(inner)
        request = RequestFactory().get("/")
        middleware(request)
        assert called["value"] is False

    def test_non_strict_mode_allows_request_through_with_no_tenant(self, tenant_a: Tenant) -> None:
        observed = {}

        def inner(request: HttpRequest) -> HttpResponse:
            observed["tenant"] = get_current_tenant()
            return HttpResponse("ok")

        with override_settings(MULTITENANT={"TENANT_MODEL": "test_app.Tenant", "STRICT": False}):
            middleware = _make_middleware(inner)
            request = RequestFactory().get("/")
            response = middleware(request)

        assert response.status_code == 200
        assert observed["tenant"] is None
