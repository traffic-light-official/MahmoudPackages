"""Tests for drf_multitenant.permissions.IsTenantMember."""

from __future__ import annotations

import pytest

from drf_multitenant.context import tenant_context
from drf_multitenant.permissions import IsTenantMember
from tests.test_app.models import Author, Tenant

pytestmark = pytest.mark.django_db


class TestHasPermission:
    def test_true_when_tenant_is_set(self, tenant_a: Tenant) -> None:
        with tenant_context(tenant_a):
            assert IsTenantMember().has_permission(request=object(), view=object()) is True  # type: ignore[arg-type]

    def test_false_when_no_tenant_is_set(self) -> None:
        assert IsTenantMember().has_permission(request=object(), view=object()) is False  # type: ignore[arg-type]


class TestHasObjectPermission:
    def test_true_for_object_belonging_to_current_tenant(self, tenant_a: Tenant) -> None:
        with tenant_context(tenant_a):
            author = Author.objects.create(name="Alice")
            assert (
                IsTenantMember().has_object_permission(request=object(), view=object(), obj=author)  # type: ignore[arg-type]
                is True
            )

    def test_false_for_object_belonging_to_a_different_tenant(
        self, tenant_a: Tenant, tenant_b: Tenant
    ) -> None:
        with tenant_context(tenant_a):
            author = Author.objects.create(name="Alice")
        with tenant_context(tenant_b):
            assert (
                IsTenantMember().has_object_permission(request=object(), view=object(), obj=author)  # type: ignore[arg-type]
                is False
            )

    def test_false_when_no_tenant_is_set(self, tenant_a: Tenant) -> None:
        with tenant_context(tenant_a):
            author = Author.objects.create(name="Alice")
        assert (
            IsTenantMember().has_object_permission(request=object(), view=object(), obj=author)  # type: ignore[arg-type]
            is False
        )
