"""Tests for drf_multitenant.testing."""

from __future__ import annotations

import pytest

from drf_multitenant.context import get_current_tenant, tenant_context
from drf_multitenant.exceptions import TenantLeakError
from drf_multitenant.testing import as_no_tenant, as_tenant, assert_no_cross_tenant_leak
from tests.test_app.models import Author, Tenant

pytestmark = pytest.mark.django_db


class TestAsTenant:
    def test_is_an_alias_for_tenant_context(self, tenant_a: Tenant) -> None:
        assert as_tenant is tenant_context

    def test_binds_tenant_for_the_block(self, tenant_a: Tenant) -> None:
        with as_tenant(tenant_a):
            assert get_current_tenant() == tenant_a
        assert get_current_tenant() is None


class TestAsNoTenant:
    def test_clears_tenant_context(self, tenant_a: Tenant) -> None:
        with tenant_context(tenant_a):
            with as_no_tenant():
                assert get_current_tenant() is None
            assert get_current_tenant() == tenant_a


class TestAssertNoCrossTenantLeak:
    def test_passes_when_all_rows_belong_to_expected_tenant(self, tenant_a: Tenant) -> None:
        with tenant_context(tenant_a):
            Author.objects.create(name="Alice")
            Author.objects.create(name="Bob")
            rows = list(Author.objects.all())
        assert_no_cross_tenant_leak(rows, tenant_a)

    def test_raises_when_a_row_belongs_to_a_different_tenant(
        self, tenant_a: Tenant, tenant_b: Tenant
    ) -> None:
        with tenant_context(tenant_a):
            good = Author.objects.create(name="Alice")
        with tenant_context(tenant_b):
            leaked = Author.objects.create(name="Bob")

        with pytest.raises(TenantLeakError, match="Author"):
            assert_no_cross_tenant_leak([good, leaked], tenant_a)

    def test_accepts_raw_pk_as_expected_tenant(self, tenant_a: Tenant) -> None:
        with tenant_context(tenant_a):
            author = Author.objects.create(name="Alice")
        assert_no_cross_tenant_leak([author], tenant_a.pk)

    def test_empty_rows_always_passes(self, tenant_a: Tenant) -> None:
        assert_no_cross_tenant_leak([], tenant_a)
