"""Tests for :mod:`drf_serializer_performance_profiler.mixins` at the serializer level."""

from __future__ import annotations

import logging

import pytest
from django.test import override_settings

from drf_serializer_performance_profiler.mixins import ProfileSerializerMixin
from drf_serializer_performance_profiler.profiling import get_serializer_profile
from tests.test_app.serializers import ArticleSerializer

pytestmark = pytest.mark.django_db


class TestOutputIsUnchanged:
    """The whole point of this package: never change what gets serialized."""

    def test_disabled_output_matches_enabled_output(self, make_article) -> None:
        article = make_article(title="Same Output", comment_count=3)

        with override_settings(SERIALIZER_PROFILER={"ENABLED": False, "LOG_SLOW_FIELDS": False}):
            disabled_data = ArticleSerializer(article).data

        with override_settings(SERIALIZER_PROFILER={"ENABLED": True}):
            enabled_data = ArticleSerializer(article).data

        assert dict(disabled_data) == dict(enabled_data)

    def test_output_matches_a_plain_modelserializer(self, make_article) -> None:
        from rest_framework import serializers

        from tests.test_app.models import Article as ArticleModel

        class PlainArticleSerializer(serializers.ModelSerializer[ArticleModel]):
            comment_count = serializers.SerializerMethodField()

            class Meta:
                model = ArticleModel
                fields = ["id", "title", "author", "comment_count"]

            def get_comment_count(self, obj: ArticleModel) -> int:
                return obj.comments.count()  # type: ignore[attr-defined]

        article = make_article(title="Parity Check", comment_count=2)

        with override_settings(SERIALIZER_PROFILER={"ENABLED": True}):
            profiled_data = ArticleSerializer(article).data
        plain_data = PlainArticleSerializer(article).data

        assert dict(profiled_data) == dict(plain_data)


class TestFastPathWhenDisabled:
    def test_no_profile_recorded_when_both_settings_are_off(self, make_article) -> None:
        article = make_article()
        with override_settings(SERIALIZER_PROFILER={"ENABLED": False, "LOG_SLOW_FIELDS": False}):
            serializer = ArticleSerializer(article)
            _ = serializer.data
        assert get_serializer_profile(serializer) is None


class TestPerFieldQueryCounts:
    def test_comment_count_field_query_count_matches_comments(self, make_article) -> None:
        article = make_article(comment_count=4)
        with override_settings(SERIALIZER_PROFILER={"ENABLED": True}):
            serializer = ArticleSerializer(article)
            _ = serializer.data

        profile = get_serializer_profile(serializer)
        assert profile is not None
        assert profile.fields["comment_count"].query_count == 1
        assert profile.fields["comment_count"].call_count == 1

    def test_title_and_author_fields_cost_no_queries(self, make_article) -> None:
        article = make_article(comment_count=2)
        with override_settings(SERIALIZER_PROFILER={"ENABLED": True}):
            serializer = ArticleSerializer(article)
            _ = serializer.data

        profile = get_serializer_profile(serializer)
        assert profile is not None
        assert profile.fields["title"].query_count == 0
        assert profile.fields["author"].query_count == 0

    def test_many_true_aggregates_across_every_row(self, make_author) -> None:
        author = make_author()
        from tests.test_app.models import Article, Comment

        for i in range(3):
            article = Article.objects.create(title=f"Article {i}", author=author)
            for _ in range(2):
                Comment.objects.create(article=article, body="hi")

        with override_settings(SERIALIZER_PROFILER={"ENABLED": True}):
            serializer = ArticleSerializer(Article.objects.all(), many=True)
            _ = serializer.data

        profile = get_serializer_profile(serializer.child)
        assert profile is not None
        assert profile.fields["comment_count"].call_count == 3
        assert profile.fields["comment_count"].query_count == 3


class TestSkippedAndNoneFields:
    def test_missing_source_attribute_is_skipped_and_not_recorded(self, make_article) -> None:
        from rest_framework import serializers

        from tests.test_app.models import Article as ArticleModel

        class _WithMissingSource(ProfileSerializerMixin, serializers.ModelSerializer[ArticleModel]):
            # No `default`, `allow_null`, or matching attribute - Field.get_attribute()
            # raises SkipField() for this combination (see DRF's fields.py).
            missing = serializers.CharField(source="nonexistent_attr", required=False)

            class Meta:
                model = ArticleModel
                fields = ["id", "title", "missing"]

        article = make_article()
        with override_settings(SERIALIZER_PROFILER={"ENABLED": True}):
            serializer = _WithMissingSource(article)
            data = serializer.data

        assert "missing" not in data
        profile = get_serializer_profile(serializer)
        assert profile is not None
        assert "missing" not in profile.fields
        assert "title" in profile.fields

    def test_write_only_field_is_skipped_and_not_recorded(self, make_article) -> None:
        from rest_framework import serializers

        from tests.test_app.models import Article as ArticleModel

        class _WithWriteOnly(ProfileSerializerMixin, serializers.ModelSerializer[ArticleModel]):
            secret = serializers.CharField(write_only=True, required=False, default="x")

            class Meta:
                model = ArticleModel
                fields = ["id", "title", "secret"]

        article = make_article()
        with override_settings(SERIALIZER_PROFILER={"ENABLED": True}):
            serializer = _WithWriteOnly(article)
            data = serializer.data

        assert "secret" not in data
        profile = get_serializer_profile(serializer)
        assert profile is not None
        assert "secret" not in profile.fields

    def test_none_valued_field_is_recorded_with_none_output(self, make_author) -> None:
        from rest_framework import serializers

        from tests.test_app.models import Article as ArticleModel

        class _WithNullableTitle(ProfileSerializerMixin, serializers.ModelSerializer[ArticleModel]):
            title = serializers.CharField(allow_null=True, required=False)

            class Meta:
                model = ArticleModel
                fields = ["id", "title"]

        author = make_author()
        from tests.test_app.models import Article

        article = Article(title=None, author=author)

        with override_settings(SERIALIZER_PROFILER={"ENABLED": True}):
            serializer = _WithNullableTitle(article)
            data = serializer.data

        assert data["title"] is None
        profile = get_serializer_profile(serializer)
        assert profile is not None
        assert "title" in profile.fields
        assert profile.fields["title"].call_count == 1


class TestLogSlowFields:
    def test_logs_a_warning_when_threshold_is_zero(self, make_article, caplog) -> None:
        article = make_article(comment_count=1)
        with (
            override_settings(
                SERIALIZER_PROFILER={"LOG_SLOW_FIELDS": True, "SLOW_FIELD_THRESHOLD_MS": 0.0}
            ),
            caplog.at_level(logging.WARNING, logger="drf_serializer_performance_profiler"),
        ):
            _ = ArticleSerializer(article).data

        assert any("comment_count" in record.message for record in caplog.records)

    def test_does_not_log_when_threshold_is_very_high(self, make_article, caplog) -> None:
        article = make_article(comment_count=1)
        with (
            override_settings(
                SERIALIZER_PROFILER={
                    "LOG_SLOW_FIELDS": True,
                    "SLOW_FIELD_THRESHOLD_MS": 999_999.0,
                }
            ),
            caplog.at_level(logging.WARNING, logger="drf_serializer_performance_profiler"),
        ):
            _ = ArticleSerializer(article).data

        assert caplog.records == []

    def test_log_slow_fields_works_even_when_enabled_is_false(self, make_article, caplog) -> None:
        article = make_article(comment_count=1)
        with (
            override_settings(
                SERIALIZER_PROFILER={
                    "ENABLED": False,
                    "LOG_SLOW_FIELDS": True,
                    "SLOW_FIELD_THRESHOLD_MS": 0.0,
                }
            ),
            caplog.at_level(logging.WARNING, logger="drf_serializer_performance_profiler"),
        ):
            _ = ArticleSerializer(article).data

        assert len(caplog.records) > 0
