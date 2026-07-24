"""End-to-end tests: real HTTP requests through TenantMiddleware and the test app's views."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from drf_multitenant.context import tenant_context
from tests.test_app.models import Article, Author, Tenant

pytestmark = pytest.mark.django_db


def _tenant_header(tenant: Tenant) -> str:
    return str(tenant.pk)


class TestRequestsWithoutATenant:
    def test_rejected_with_400_when_no_header_given(self, client: APIClient) -> None:
        response = client.get("/articles/")
        assert response.status_code == 400


class TestListIsolation:
    def test_list_only_returns_current_tenants_rows(
        self, client: APIClient, tenant_a: Tenant, tenant_b: Tenant
    ) -> None:
        with tenant_context(tenant_a):
            author_a = Author.objects.create(name="Alice")
            Article.objects.create(author=author_a, title="A's article")
        with tenant_context(tenant_b):
            author_b = Author.objects.create(name="Bob")
            Article.objects.create(author=author_b, title="B's article")

        response = client.get("/articles/", HTTP_X_TENANT_ID=_tenant_header(tenant_a))
        assert response.status_code == 200
        titles = {row["title"] for row in response.json()}
        assert titles == {"A's article"}


class TestDetailIsolation:
    def test_other_tenants_object_is_not_found(
        self, client: APIClient, tenant_a: Tenant, tenant_b: Tenant
    ) -> None:
        with tenant_context(tenant_b):
            author_b = Author.objects.create(name="Bob")
            article_b = Article.objects.create(author=author_b, title="B's article")

        response = client.get(
            f"/articles/{article_b.pk}/", HTTP_X_TENANT_ID=_tenant_header(tenant_a)
        )
        assert response.status_code == 404

    def test_own_tenants_object_is_found(self, client: APIClient, tenant_a: Tenant) -> None:
        with tenant_context(tenant_a):
            author_a = Author.objects.create(name="Alice")
            article_a = Article.objects.create(author=author_a, title="A's article")

        response = client.get(
            f"/articles/{article_a.pk}/", HTTP_X_TENANT_ID=_tenant_header(tenant_a)
        )
        assert response.status_code == 200
        assert response.json()["title"] == "A's article"


class TestCreateAutoAssignsTenant:
    def test_created_article_belongs_to_the_requesting_tenant(
        self, client: APIClient, tenant_a: Tenant
    ) -> None:
        with tenant_context(tenant_a):
            author_a = Author.objects.create(name="Alice")

        response = client.post(
            "/articles/",
            data={"author": author_a.pk, "title": "New Article"},
            HTTP_X_TENANT_ID=_tenant_header(tenant_a),
        )
        assert response.status_code == 201
        assert response.json()["tenant"] == tenant_a.pk

    def test_cannot_create_an_article_referencing_another_tenants_author(
        self, client: APIClient, tenant_a: Tenant, tenant_b: Tenant
    ) -> None:
        with tenant_context(tenant_b):
            other_author = Author.objects.create(name="Bob")

        response = client.post(
            "/articles/",
            data={"author": other_author.pk, "title": "New Article"},
            HTTP_X_TENANT_ID=_tenant_header(tenant_a),
        )
        assert response.status_code == 400


class TestCrossTenantWriteIsBlockedEndToEnd:
    def test_cannot_update_another_tenants_article(
        self, client: APIClient, tenant_a: Tenant, tenant_b: Tenant
    ) -> None:
        with tenant_context(tenant_b):
            author_b = Author.objects.create(name="Bob")
            article_b = Article.objects.create(author=author_b, title="B's article")

        response = client.patch(
            f"/articles/{article_b.pk}/",
            data={"title": "Hijacked"},
            HTTP_X_TENANT_ID=_tenant_header(tenant_a),
        )
        # Not found from tenant_a's perspective — the queryset never
        # exposes article_b's row to begin with.
        assert response.status_code == 404
