"""Tests for drf_multitenant.managers."""

from __future__ import annotations

import pytest

from drf_multitenant.context import tenant_context
from drf_multitenant.managers import tenant_pk
from tests.test_app.models import Article, Author, Tenant


@pytest.fixture
def article_a(tenant_a: Tenant) -> Article:
    with tenant_context(tenant_a):
        author = Author.objects.create(name="Alice")
        article: Article = Article.objects.create(author=author, title="A's article")
        return article


@pytest.fixture
def article_b(tenant_b: Tenant) -> Article:
    with tenant_context(tenant_b):
        author = Author.objects.create(name="Bob")
        article: Article = Article.objects.create(author=author, title="B's article")
        return article


@pytest.mark.django_db
class TestTenantScoping:
    def test_objects_returns_only_current_tenant_rows(
        self, tenant_a: Tenant, article_a: Article, article_b: Article
    ) -> None:
        with tenant_context(tenant_a):
            titles = set(Article.objects.values_list("title", flat=True))
        assert titles == {"A's article"}

    def test_objects_returns_empty_queryset_when_no_tenant_set(
        self, article_a: Article, article_b: Article
    ) -> None:
        assert list(Article.objects.all()) == []

    def test_objects_all_does_not_raise_at_construction_time(self) -> None:
        # Regression: this must not raise even with no tenant context —
        # it's the exact pattern PrimaryKeyRelatedField(queryset=...) uses
        # in a serializer class body, long before any request exists.
        qs = Article.objects.all()
        assert list(qs) == []

    def test_switching_tenant_context_changes_visible_rows(
        self, tenant_a: Tenant, tenant_b: Tenant, article_a: Article, article_b: Article
    ) -> None:
        with tenant_context(tenant_a):
            assert Article.objects.count() == 1
        with tenant_context(tenant_b):
            assert Article.objects.count() == 1
            assert Article.objects.first().title == "B's article"  # type: ignore[union-attr]


@pytest.mark.django_db
class TestUnscoped:
    def test_unscoped_returns_every_tenants_rows(
        self, article_a: Article, article_b: Article
    ) -> None:
        with tenant_context(article_a.tenant):
            titles = set(Article.objects.unscoped().values_list("title", flat=True))
        assert titles == {"A's article", "B's article"}

    def test_unscoped_works_with_no_tenant_set(
        self, article_a: Article, article_b: Article
    ) -> None:
        assert Article.objects.unscoped().count() == 2

    def test_unscoped_logs_a_warning(
        self, article_a: Article, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level("WARNING", logger="drf_multitenant"):
            Article.objects.unscoped().count()
        assert any("Unscoped" in record.message for record in caplog.records)


@pytest.mark.django_db
class TestAllTenantsManager:
    def test_all_tenants_manager_is_unfiltered(
        self, article_a: Article, article_b: Article
    ) -> None:
        assert Article.all_tenants.count() == 2


class TestTenantPk:
    def test_extracts_pk_from_instance(self, db: None) -> None:
        tenant = Tenant.objects.create(name="Acme", slug="acme")
        assert tenant_pk(tenant) == tenant.pk

    def test_passes_through_raw_pk(self) -> None:
        assert tenant_pk(42) == 42
