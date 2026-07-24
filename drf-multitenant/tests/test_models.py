"""Tests for drf_multitenant.models.TenantScopedModel."""

from __future__ import annotations

import pytest

from drf_multitenant.context import tenant_context
from drf_multitenant.exceptions import NoTenantSetError, TenantMismatchError
from tests.test_app.models import Author, Tenant


@pytest.mark.django_db
class TestSaveAutoAssign:
    def test_assigns_current_tenant_on_create_when_unset(self, tenant_a: Tenant) -> None:
        with tenant_context(tenant_a):
            author = Author(name="Alice")
            author.save()
        assert author.tenant_id == tenant_a.pk

    def test_raises_when_no_tenant_assigned_and_none_current(self) -> None:
        author = Author(name="Alice")
        with pytest.raises(NoTenantSetError):
            author.save()

    def test_explicit_tenant_assignment_is_respected_with_no_current_tenant(
        self, tenant_a: Tenant
    ) -> None:
        author = Author(name="Alice", tenant=tenant_a)
        author.save()
        assert author.tenant_id == tenant_a.pk


@pytest.mark.django_db
class TestSaveMismatchGuard:
    def test_raises_when_saving_under_a_different_tenant_context(
        self, tenant_a: Tenant, tenant_b: Tenant
    ) -> None:
        with tenant_context(tenant_a):
            author = Author.objects.create(name="Alice")

        with tenant_context(tenant_b):
            author.name = "Alice Renamed"
            with pytest.raises(TenantMismatchError):
                author.save()

    def test_saving_under_the_same_tenant_context_succeeds(self, tenant_a: Tenant) -> None:
        with tenant_context(tenant_a):
            author = Author.objects.create(name="Alice")
            author.name = "Alice Renamed"
            author.save()
        assert Author.all_tenants.get(pk=author.pk).name == "Alice Renamed"

    def test_saving_with_no_current_tenant_does_not_raise_mismatch(self, tenant_a: Tenant) -> None:
        # No current tenant means nothing to compare against — only an
        # actual mismatch (both sides set, and different) should raise.
        with tenant_context(tenant_a):
            author = Author.objects.create(name="Alice")
        author.name = "Alice Renamed"
        author.save()
        assert Author.all_tenants.get(pk=author.pk).name == "Alice Renamed"
