"""Tests for drf_multitenant.admin.TenantAdminMixin."""

from __future__ import annotations

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.test import RequestFactory

from drf_multitenant.admin import TenantAdminMixin
from drf_multitenant.context import tenant_context
from tests.test_app.models import Author, Tenant

pytestmark = pytest.mark.django_db


class AuthorAdmin(TenantAdminMixin):
    pass


@pytest.fixture
def author_admin() -> AuthorAdmin:
    return AuthorAdmin(Author, admin.site)


def _request(is_superuser: bool = False) -> HttpRequest:
    request = RequestFactory().get("/admin/")
    user = get_user_model().objects.create_user(
        username="staff", is_staff=True, is_superuser=is_superuser
    )
    request.user = user
    return request


class TestTenantAdminMixin:
    def test_non_superuser_sees_only_current_tenant_rows(
        self, author_admin: AuthorAdmin, tenant_a: Tenant, tenant_b: Tenant
    ) -> None:
        with tenant_context(tenant_a):
            Author.objects.create(name="Alice")
        with tenant_context(tenant_b):
            Author.objects.create(name="Bob")

        with tenant_context(tenant_a):
            qs = author_admin.get_queryset(_request(is_superuser=False))
        assert list(qs.values_list("name", flat=True)) == ["Alice"]

    def test_superuser_sees_every_tenants_rows(
        self, author_admin: AuthorAdmin, tenant_a: Tenant, tenant_b: Tenant
    ) -> None:
        with tenant_context(tenant_a):
            Author.objects.create(name="Alice")
        with tenant_context(tenant_b):
            Author.objects.create(name="Bob")

        qs = author_admin.get_queryset(_request(is_superuser=True))
        assert set(qs.values_list("name", flat=True)) == {"Alice", "Bob"}

    def test_non_superuser_with_no_tenant_sees_nothing(
        self, author_admin: AuthorAdmin, tenant_a: Tenant
    ) -> None:
        with tenant_context(tenant_a):
            Author.objects.create(name="Alice")

        qs = author_admin.get_queryset(_request(is_superuser=False))
        assert list(qs) == []
