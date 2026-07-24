"""Tests for drf_multitenant.resolvers."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory, override_settings

from drf_multitenant.resolvers import (
    header_resolver,
    resolve_tenant,
    subdomain_resolver,
    user_attr_resolver,
)
from tests.test_app.models import Tenant

pytestmark = pytest.mark.django_db


class TestHeaderResolver:
    def test_resolves_tenant_from_header(self, tenant_a: Tenant) -> None:
        request = RequestFactory().get("/", HTTP_X_TENANT_ID=str(tenant_a.pk))
        assert header_resolver(request) == tenant_a

    def test_returns_none_when_header_absent(self) -> None:
        request = RequestFactory().get("/")
        assert header_resolver(request) is None

    def test_returns_none_when_header_value_does_not_match_any_tenant(self) -> None:
        request = RequestFactory().get("/", HTTP_X_TENANT_ID="999999")
        assert header_resolver(request) is None

    def test_honors_custom_header_name_setting(self, tenant_a: Tenant) -> None:
        with override_settings(
            MULTITENANT={"TENANT_MODEL": "test_app.Tenant", "TENANT_HEADER": "X-Org-ID"}
        ):
            request = RequestFactory().get("/", HTTP_X_ORG_ID=str(tenant_a.pk))
            assert header_resolver(request) == tenant_a

    def test_raises_when_tenant_model_not_configured(self, tenant_a: Tenant) -> None:
        with override_settings(MULTITENANT={}):
            request = RequestFactory().get("/", HTTP_X_TENANT_ID=str(tenant_a.pk))
            with pytest.raises(ImproperlyConfigured, match="TENANT_MODEL"):
                header_resolver(request)


class TestSubdomainResolver:
    def test_resolves_tenant_from_subdomain(self, tenant_a: Tenant) -> None:
        request = RequestFactory().get("/", HTTP_HOST="acme.example.com")
        assert subdomain_resolver(request) == tenant_a

    def test_returns_none_for_bare_domain(self) -> None:
        request = RequestFactory().get("/", HTTP_HOST="example.com")
        assert subdomain_resolver(request) is None

    def test_returns_none_for_unknown_subdomain(self) -> None:
        request = RequestFactory().get("/", HTTP_HOST="nobody.example.com")
        assert subdomain_resolver(request) is None

    def test_ignores_port_in_host(self, tenant_a: Tenant) -> None:
        request = RequestFactory().get("/", HTTP_HOST="acme.example.com:8000")
        assert subdomain_resolver(request) == tenant_a


class TestUserAttrResolver:
    def test_resolves_tenant_from_authenticated_user(self, tenant_a: Tenant) -> None:
        user = get_user_model().objects.create_user(username="alice")
        user.tenant = tenant_a  # type: ignore[attr-defined]
        request = RequestFactory().get("/")
        request.user = user
        assert user_attr_resolver(request) == tenant_a

    def test_returns_none_for_unauthenticated_user(self) -> None:
        from django.contrib.auth.models import AnonymousUser

        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        assert user_attr_resolver(request) is None

    def test_returns_none_when_user_has_no_tenant_attribute(self) -> None:
        user = get_user_model().objects.create_user(username="alice")
        request = RequestFactory().get("/")
        request.user = user
        assert user_attr_resolver(request) is None

    def test_honors_custom_attr_name_setting(self, tenant_a: Tenant) -> None:
        user = get_user_model().objects.create_user(username="alice")
        user.org = tenant_a  # type: ignore[attr-defined]
        request = RequestFactory().get("/")
        request.user = user
        with override_settings(
            MULTITENANT={"TENANT_MODEL": "test_app.Tenant", "USER_TENANT_ATTR": "org"}
        ):
            assert user_attr_resolver(request) == tenant_a


class TestResolveTenant:
    def test_dispatches_to_configured_resolver(self, tenant_a: Tenant) -> None:
        request = RequestFactory().get("/", HTTP_X_TENANT_ID=str(tenant_a.pk))
        assert resolve_tenant(request) == tenant_a

    def test_dispatches_to_a_custom_resolver_path(self) -> None:
        with override_settings(
            MULTITENANT={
                "TENANT_MODEL": "test_app.Tenant",
                "RESOLVER": "drf_multitenant.resolvers.user_attr_resolver",
            }
        ):
            request = RequestFactory().get("/")
            from django.contrib.auth.models import AnonymousUser

            request.user = AnonymousUser()
            assert resolve_tenant(request) is None
