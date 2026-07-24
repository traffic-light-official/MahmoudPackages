"""Tests for drf_multitenant.serializers."""

from __future__ import annotations

import pytest
from rest_framework import serializers

from drf_multitenant.context import tenant_context
from drf_multitenant.exceptions import CrossTenantReferenceError, TenantMismatchError
from drf_multitenant.serializers import TenantScopedModelSerializer, _iter_model_instances
from tests.test_app.models import Article, Author, Tenant
from tests.test_app.serializers import ArticleSerializer, AuthorSerializer

pytestmark = pytest.mark.django_db


class TestAutoAssignOnCreate:
    def test_tenant_injected_when_not_provided(self, tenant_a: Tenant) -> None:
        with tenant_context(tenant_a):
            serializer = AuthorSerializer(data={"name": "Alice"})
            assert serializer.is_valid(), serializer.errors
            author = serializer.save()
        assert author.tenant_id == tenant_a.pk

    def test_already_present_tenant_is_not_overwritten(self, tenant_a: Tenant) -> None:
        # tenant is a read_only field in the test serializer, so it can't
        # actually arrive via input data — set it directly on
        # validated_data to exercise the mixin's "don't overwrite an
        # already-present value" branch in isolation. Uses the *same*
        # tenant as the current context so this doesn't also trigger the
        # model-level mismatch guard (tested separately, below).
        with tenant_context(tenant_a):
            serializer = AuthorSerializer(data={"name": "Alice"})
            assert serializer.is_valid()
            serializer.validated_data["tenant"] = tenant_a
            author = serializer.save()
        assert author.tenant_id == tenant_a.pk

    def test_assigning_a_different_tenant_than_current_context_is_rejected(
        self, tenant_a: Tenant, tenant_b: Tenant
    ) -> None:
        # The model-level save() guard (TenantScopedModel) still applies
        # underneath the serializer — assigning a tenant that mismatches
        # the current context is a save-time error regardless of which
        # layer set the field.
        with tenant_context(tenant_a):
            serializer = AuthorSerializer(data={"name": "Alice"})
            assert serializer.is_valid()
            serializer.validated_data["tenant"] = tenant_b
            with pytest.raises(TenantMismatchError):
                serializer.save()


class TestCrossTenantReferenceValidation:
    def test_referencing_an_author_from_a_different_tenant_is_rejected_at_the_field_level(
        self, tenant_a: Tenant, tenant_b: Tenant
    ) -> None:
        # ArticleSerializer's `author` field is auto-built by
        # ModelSerializer from the FK, which uses Author.objects (tenant-
        # scoped) as its queryset — so a cross-tenant author id is
        # already rejected by ordinary field validation ("does not
        # exist"), before the mixin's own validate() check even runs.
        # This is the primary, preferred defense: the mixin's check
        # below is for cases where that automatic scoping was bypassed.
        with tenant_context(tenant_b):
            other_author = Author.objects.create(name="Bob")

        with tenant_context(tenant_a):
            serializer = ArticleSerializer(data={"author": other_author.pk, "title": "Hi"})
            assert not serializer.is_valid()
            assert "does_not_exist" in str(serializer.errors["author"][0].code)

    def test_referencing_an_author_from_the_same_tenant_is_allowed(self, tenant_a: Tenant) -> None:
        with tenant_context(tenant_a):
            author = Author.objects.create(name="Alice")
            serializer = ArticleSerializer(data={"author": author.pk, "title": "Hi"})
            assert serializer.is_valid(), serializer.errors
            article = serializer.save()
        assert article.author_id == author.pk
        assert article.tenant_id == tenant_a.pk

    def test_mixin_rejects_cross_tenant_reference_when_field_scoping_is_bypassed(
        self, tenant_a: Tenant, tenant_b: Tenant
    ) -> None:
        # Simulates a field explicitly built against an *unscoped*
        # queryset (Author.all_tenants.all()) — e.g. a developer opting
        # into broader lookup for some other reason. The mixin's own
        # validate() check is the defense-in-depth layer that still
        # catches this.
        class UnscopedAuthorArticleSerializer(TenantScopedModelSerializer):
            author = serializers.PrimaryKeyRelatedField(queryset=Author.all_tenants.all())

            class Meta:
                model = Article
                fields = ["id", "tenant", "author", "title"]
                read_only_fields = ["id", "tenant"]

        with tenant_context(tenant_b):
            other_author = Author.objects.create(name="Bob")

        with tenant_context(tenant_a):
            serializer = UnscopedAuthorArticleSerializer(
                data={"author": other_author.pk, "title": "Hi"}
            )
            with pytest.raises(CrossTenantReferenceError):
                serializer.is_valid(raise_exception=True)


class TestIterModelInstances:
    def test_yields_a_single_model_instance(self, tenant_a: Tenant) -> None:
        with tenant_context(tenant_a):
            author = Author.objects.create(name="Alice")
        assert list(_iter_model_instances(author)) == [author]

    def test_yields_from_a_list_of_model_instances(self, tenant_a: Tenant) -> None:
        with tenant_context(tenant_a):
            author1 = Author.objects.create(name="Alice")
            author2 = Author.objects.create(name="Bob")
        assert list(_iter_model_instances([author1, author2])) == [author1, author2]

    def test_yields_from_a_queryset(self, tenant_a: Tenant) -> None:
        with tenant_context(tenant_a):
            Author.objects.create(name="Alice")
            qs = Author.objects.all()
        assert list(_iter_model_instances(qs)) == list(qs)

    def test_yields_nothing_for_non_model_values(self) -> None:
        assert list(_iter_model_instances("just a string")) == []
        assert list(_iter_model_instances(42)) == []
        assert list(_iter_model_instances(None)) == []

    def test_many_related_field_with_cross_tenant_member_is_rejected(
        self, tenant_a: Tenant, tenant_b: Tenant
    ) -> None:
        class ManyAuthorsSerializer(TenantScopedModelSerializer):
            authors = serializers.PrimaryKeyRelatedField(
                many=True, queryset=Author.all_tenants.all()
            )

            class Meta:
                model = Article
                fields = ["id", "tenant", "authors", "title"]
                read_only_fields = ["id", "tenant"]

        with tenant_context(tenant_a):
            own_author = Author.objects.create(name="Alice")
        with tenant_context(tenant_b):
            other_author = Author.objects.create(name="Bob")

        with tenant_context(tenant_a):
            serializer = ManyAuthorsSerializer(
                data={"authors": [own_author.pk, other_author.pk], "title": "Hi"}
            )
            with pytest.raises(CrossTenantReferenceError):
                serializer.is_valid(raise_exception=True)
