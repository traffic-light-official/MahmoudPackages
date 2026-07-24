"""Tests for drf_multitenant.cache."""

from __future__ import annotations

import pytest
from django.test import override_settings

from drf_multitenant.cache import get_tenant_cache, tenant_cache_key
from drf_multitenant.context import tenant_context
from drf_multitenant.exceptions import NoTenantSetError
from tests.test_app.models import Tenant

pytestmark = pytest.mark.django_db

CACHES_SETTING = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-cache",
    }
}


@pytest.fixture
def _locmem_cache(settings: object) -> None:
    settings.CACHES = CACHES_SETTING  # type: ignore[attr-defined]


class TestTenantCacheKey:
    def test_namespaces_by_current_tenant(self, tenant_a: Tenant) -> None:
        with tenant_context(tenant_a):
            key = tenant_cache_key("my-key")
        assert key == f"tenant:{tenant_a.pk}:my-key"

    def test_different_tenants_produce_different_keys(
        self, tenant_a: Tenant, tenant_b: Tenant
    ) -> None:
        with tenant_context(tenant_a):
            key_a = tenant_cache_key("my-key")
        with tenant_context(tenant_b):
            key_b = tenant_cache_key("my-key")
        assert key_a != key_b

    def test_explicit_tenant_argument_overrides_context(
        self, tenant_a: Tenant, tenant_b: Tenant
    ) -> None:
        with tenant_context(tenant_a):
            key = tenant_cache_key("my-key", tenant=tenant_b)
        assert key == f"tenant:{tenant_b.pk}:my-key"

    def test_raises_when_no_tenant_available(self) -> None:
        with pytest.raises(NoTenantSetError):
            tenant_cache_key("my-key")

    def test_honors_custom_prefix_setting(self, tenant_a: Tenant) -> None:
        with (
            override_settings(
                MULTITENANT={"TENANT_MODEL": "test_app.Tenant", "CACHE_KEY_PREFIX": "org"}
            ),
            tenant_context(tenant_a),
        ):
            key = tenant_cache_key("my-key")
        assert key == f"org:{tenant_a.pk}:my-key"


@pytest.mark.usefixtures("_locmem_cache")
class TestTenantCache:
    def test_get_set_delete_roundtrip(self, tenant_a: Tenant) -> None:
        cache = get_tenant_cache()
        with tenant_context(tenant_a):
            cache.set("counter", 1)
            assert cache.get("counter") == 1
            cache.delete("counter")
            assert cache.get("counter") is None

    def test_get_default_when_missing(self, tenant_a: Tenant) -> None:
        cache = get_tenant_cache()
        with tenant_context(tenant_a):
            assert cache.get("missing", "fallback") == "fallback"

    def test_isolated_between_tenants(self, tenant_a: Tenant, tenant_b: Tenant) -> None:
        cache = get_tenant_cache()
        with tenant_context(tenant_a):
            cache.set("shared-key", "a-value")
        with tenant_context(tenant_b):
            assert cache.get("shared-key") is None
            cache.set("shared-key", "b-value")
        with tenant_context(tenant_a):
            assert cache.get("shared-key") == "a-value"

    def test_get_or_set(self, tenant_a: Tenant) -> None:
        cache = get_tenant_cache()
        with tenant_context(tenant_a):
            assert cache.get_or_set("computed", lambda: "value") == "value"
            assert cache.get("computed") == "value"

    def test_incr_decr(self, tenant_a: Tenant) -> None:
        cache = get_tenant_cache()
        with tenant_context(tenant_a):
            cache.set("counter", 1)
            assert cache.incr("counter") == 2
            assert cache.decr("counter") == 1

    def test_clear_tenant_not_implemented_by_default(self, tenant_a: Tenant) -> None:
        cache = get_tenant_cache()
        with tenant_context(tenant_a), pytest.raises(NotImplementedError):
            cache.clear_tenant()

    def test_custom_alias(self, tenant_a: Tenant) -> None:
        cache = get_tenant_cache("default")
        with tenant_context(tenant_a):
            cache.set("x", 1)
            assert cache.get("x") == 1
