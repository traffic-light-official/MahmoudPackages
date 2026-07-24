"""Tests for automatic queryset optimization, including N+1 prevention."""

from __future__ import annotations

import pytest
from django.db import connection
from django.db.models import Count, Prefetch
from django.test.utils import CaptureQueriesContext

from drf_partial_response_fields.constants import CONTEXT_KEY
from drf_partial_response_fields.optimizer import optimize_queryset
from drf_partial_response_fields.parser import parse_fields
from tests.test_app.models import Article
from tests.test_app.serializers import (
    ArticlePKAuthorSerializer,
    ArticleSerializer,
    ArticleWithTagCountSerializer,
)

pytestmark = pytest.mark.django_db


class TestSelectRelated:
    def test_nested_serializer_relation_adds_select_related(self, article: Article) -> None:
        tree = parse_fields("title,author(name)")
        qs = optimize_queryset(Article.objects.all(), ArticleSerializer, tree)
        assert "author" in qs.query.select_related

    def test_pk_only_relation_does_not_add_select_related(self, article: Article) -> None:
        tree = parse_fields("title,author")
        qs = optimize_queryset(Article.objects.all(), ArticlePKAuthorSerializer, tree)
        assert qs.query.select_related is False

    def test_deeply_nested_relation_adds_chained_select_related(
        self, article: Article, profile: object
    ) -> None:
        tree = parse_fields("author(profile(display_name))")
        qs = optimize_queryset(Article.objects.all(), ArticleSerializer, tree)
        assert qs.query.select_related == {"author": {"profile": {}}}

    def test_editor_note_method_field_hint_adds_select_related(self, article: Article) -> None:
        tree = parse_fields("editor_note")
        qs = optimize_queryset(Article.objects.all(), ArticleSerializer, tree)
        assert qs.query.select_related == {"author": {"profile": {}}}

    def test_unrequested_relation_is_not_selected(self, article: Article) -> None:
        tree = parse_fields("title")
        qs = optimize_queryset(Article.objects.all(), ArticleSerializer, tree)
        assert qs.query.select_related is False


class TestPrefetchRelated:
    def test_many_to_many_field_adds_prefetch(self, article: Article) -> None:
        tree = parse_fields("title,tags(label)")
        qs = optimize_queryset(Article.objects.all(), ArticleSerializer, tree)
        lookups = qs._prefetch_related_lookups
        assert len(lookups) == 1
        assert isinstance(lookups[0], Prefetch)
        assert lookups[0].prefetch_through == "tags"

    def test_reverse_fk_field_adds_prefetch(self, article: Article) -> None:
        tree = parse_fields("title,comments(text)")
        qs = optimize_queryset(Article.objects.all(), ArticleSerializer, tree)
        lookups = qs._prefetch_related_lookups
        assert any(
            (lookup.prefetch_through if isinstance(lookup, Prefetch) else lookup) == "comments"
            for lookup in lookups
        )

    def test_unrequested_many_relation_is_not_prefetched(self, article: Article) -> None:
        tree = parse_fields("title")
        qs = optimize_queryset(Article.objects.all(), ArticleSerializer, tree)
        assert qs._prefetch_related_lookups == ()

    def test_pk_only_many_relation_restricts_nested_queryset_to_pk(self, article: Article) -> None:
        tree = parse_fields("title,tags")
        qs = optimize_queryset(Article.objects.all(), ArticlePKAuthorSerializer, tree)
        lookups = qs._prefetch_related_lookups
        assert len(lookups) == 1
        assert isinstance(lookups[0], Prefetch)
        fields, defer = lookups[0].queryset.query.deferred_loading
        assert defer is False
        assert fields == frozenset({"id"})


class TestOnly:
    def test_only_includes_requested_scalar_fields(self, article: Article) -> None:
        tree = parse_fields("title,view_count")
        qs = optimize_queryset(Article.objects.all(), ArticleSerializer, tree)
        fields, defer = qs.query.deferred_loading
        assert defer is False
        # Django tracks the primary key separately from only()'s field list
        # and always loads it regardless, so it is deliberately not asserted
        # here - see https://docs.djangoproject.com/en/stable/ref/models/querysets/#only
        assert {"title", "view_count"} <= fields

    def test_only_excludes_unrequested_scalar_fields(self, article: Article) -> None:
        tree = parse_fields("title")
        qs = optimize_queryset(Article.objects.all(), ArticleSerializer, tree)
        fields, _defer = qs.query.deferred_loading
        assert "body" not in fields

    def test_only_includes_nested_relation_columns(self, article: Article) -> None:
        tree = parse_fields("author(name)")
        qs = optimize_queryset(Article.objects.all(), ArticleSerializer, tree)
        fields, defer = qs.query.deferred_loading
        assert defer is False
        assert "author__name" in fields


class TestAnnotations:
    def test_annotated_field_is_kept_in_only_without_relation_lookup(
        self, article: Article
    ) -> None:
        annotated_qs = Article.objects.annotate(tag_count=Count("tags"))
        tree = parse_fields("title,tag_count")

        qs = optimize_queryset(annotated_qs, ArticleWithTagCountSerializer, tree)
        fields, defer = qs.query.deferred_loading
        assert defer is False
        assert "tag_count" in fields
        # The annotation must not be misinterpreted as a model relation.
        assert qs.query.select_related is False


class TestSettingsIntegration:
    def test_optimization_disabled_returns_original_queryset(self, article: Article) -> None:
        from django.test import override_settings

        base_qs = Article.objects.all()
        tree = parse_fields("title,author(name)")
        with override_settings(PARTIAL_RESPONSE_FIELDS={"ENABLE_QUERY_OPTIMIZATION": False}):
            qs = optimize_queryset(base_qs, ArticleSerializer, tree)
        assert qs.query.select_related is False


class TestQueryCountReduction:
    """End-to-end proof that fewer requested fields means fewer queries."""

    def test_unoptimized_baseline_triggers_n_plus_one(self, many_articles: list[Article]) -> None:
        with CaptureQueriesContext(connection) as ctx:
            for a in Article.objects.all():
                _ = a.author.name  # forces one query per article
        assert len(ctx.captured_queries) >= len(many_articles)

    def test_full_field_optimization_collapses_to_constant_queries(self, article: Article) -> None:
        tree = parse_fields("")  # request everything
        qs = optimize_queryset(Article.objects.all(), ArticleSerializer, tree)
        serializer = ArticleSerializer(qs, many=True, context={CONTEXT_KEY: tree})
        with CaptureQueriesContext(connection) as ctx:
            _ = serializer.data
        # 1 (articles) + 1 (tags prefetch) + 1 (comments prefetch) = 3,
        # regardless of how many articles/tags/comments exist.
        assert len(ctx.captured_queries) <= 3

    def test_narrow_selection_uses_fewer_queries_than_full_selection(
        self, article: Article
    ) -> None:
        full_tree = parse_fields("")
        full_qs = optimize_queryset(Article.objects.all(), ArticleSerializer, full_tree)
        full_serializer = ArticleSerializer(full_qs, many=True, context={CONTEXT_KEY: full_tree})
        with CaptureQueriesContext(connection) as ctx_full:
            _ = full_serializer.data

        narrow_tree = parse_fields("title")
        narrow_qs = optimize_queryset(Article.objects.all(), ArticleSerializer, narrow_tree)
        narrow_serializer = ArticleSerializer(
            narrow_qs, many=True, context={CONTEXT_KEY: narrow_tree}
        )
        with CaptureQueriesContext(connection) as ctx_narrow:
            _ = narrow_serializer.data

        assert len(ctx_narrow.captured_queries) < len(ctx_full.captured_queries)
