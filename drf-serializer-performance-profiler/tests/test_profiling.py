"""Tests for :mod:`drf_serializer_performance_profiler.profiling`."""

from __future__ import annotations

import pytest

from drf_serializer_performance_profiler.profiling import (
    FieldProfile,
    SerializerProfile,
    get_serializer_profile,
    measure,
    merge_profiles,
)
from tests.test_app.models import Article

pytestmark = pytest.mark.django_db


class TestFieldProfile:
    def test_record_accumulates_across_calls(self) -> None:
        profile = FieldProfile("title")
        profile.record(10.0, 1)
        profile.record(5.0, 2)
        assert profile.total_time_ms == 15.0
        assert profile.call_count == 2
        assert profile.query_count == 3

    def test_average_time_ms(self) -> None:
        profile = FieldProfile("title")
        profile.record(10.0, 0)
        profile.record(20.0, 0)
        assert profile.average_time_ms == 15.0

    def test_average_time_ms_is_zero_when_never_called(self) -> None:
        assert FieldProfile("title").average_time_ms == 0.0

    def test_as_dict(self) -> None:
        profile = FieldProfile("title")
        profile.record(10.0, 2)
        assert profile.as_dict() == {
            "field_name": "title",
            "total_time_ms": 10.0,
            "average_time_ms": 10.0,
            "call_count": 1,
            "query_count": 2,
        }


class TestSerializerProfile:
    def test_record_creates_a_new_field_profile(self) -> None:
        profile = SerializerProfile()
        profile.record("title", 5.0, 0)
        assert "title" in profile.fields
        assert profile.fields["title"].total_time_ms == 5.0

    def test_total_time_ms_sums_every_field(self) -> None:
        profile = SerializerProfile()
        profile.record("title", 5.0, 0)
        profile.record("author", 3.0, 1)
        assert profile.total_time_ms == 8.0

    def test_total_query_count_sums_every_field(self) -> None:
        profile = SerializerProfile()
        profile.record("title", 5.0, 0)
        profile.record("comment_count", 10.0, 3)
        assert profile.total_query_count == 3

    def test_slowest_fields_orders_descending(self) -> None:
        profile = SerializerProfile()
        profile.record("fast", 1.0, 0)
        profile.record("slow", 100.0, 0)
        profile.record("medium", 10.0, 0)
        assert [f.field_name for f in profile.slowest_fields()] == ["slow", "medium", "fast"]

    def test_slowest_fields_respects_limit(self) -> None:
        profile = SerializerProfile()
        profile.record("a", 1.0, 0)
        profile.record("b", 2.0, 0)
        profile.record("c", 3.0, 0)
        assert len(profile.slowest_fields(limit=2)) == 2

    def test_as_dict(self) -> None:
        profile = SerializerProfile()
        profile.record("title", 5.0, 0)
        result = profile.as_dict()
        assert result["total_time_ms"] == 5.0
        assert result["total_query_count"] == 0
        assert result["fields"][0]["field_name"] == "title"

    def test_as_header_value_includes_total_and_queries(self) -> None:
        profile = SerializerProfile()
        profile.record("comment_count", 12.5, 3)
        header = profile.as_header_value()
        assert "comment_count=12.50ms (3q)" in header
        assert "total=12.50ms" in header
        assert "queries=3" in header

    def test_as_header_value_respects_max_fields(self) -> None:
        profile = SerializerProfile()
        for i in range(10):
            profile.record(f"field{i}", float(i), 0)
        header = profile.as_header_value(max_fields=2)
        assert header.count("=") - 2 == 2  # 2 fields, minus the "total="/"queries=" pair


class TestMergeProfiles:
    def test_merges_matching_field_names(self) -> None:
        first = SerializerProfile()
        first.record("title", 5.0, 1)
        second = SerializerProfile()
        second.record("title", 3.0, 2)

        merged = merge_profiles([first, second])
        assert merged.fields["title"].total_time_ms == 8.0
        assert merged.fields["title"].call_count == 2
        assert merged.fields["title"].query_count == 3

    def test_merges_distinct_field_names(self) -> None:
        first = SerializerProfile()
        first.record("title", 5.0, 0)
        second = SerializerProfile()
        second.record("author", 3.0, 0)

        merged = merge_profiles([first, second])
        assert set(merged.fields) == {"title", "author"}

    def test_empty_list_returns_empty_profile(self) -> None:
        merged = merge_profiles([])
        assert merged.fields == {}


class TestGetSerializerProfile:
    def test_returns_none_when_never_profiled(self) -> None:
        class _Fake:
            pass

        assert get_serializer_profile(_Fake()) is None  # type: ignore[arg-type]

    def test_returns_the_recorded_profile(self) -> None:
        class _Fake:
            pass

        fake = _Fake()
        profile = SerializerProfile()
        fake._serializer_profile = profile  # type: ignore[attr-defined]
        assert get_serializer_profile(fake) is profile  # type: ignore[arg-type]


class TestMeasure:
    def test_measures_elapsed_time_is_non_negative(self) -> None:
        with measure() as measurement:
            pass
        assert measurement.elapsed_ms >= 0

    def test_counts_zero_queries_when_none_are_made(self) -> None:
        with measure() as measurement:
            pass
        assert measurement.query_count == 0

    def test_counts_queries_made_inside_the_block(self, make_author) -> None:
        make_author()
        with measure() as measurement:
            list(Article.objects.all())
        assert measurement.query_count == 1

    def test_counts_multiple_queries(self, make_author) -> None:
        make_author()
        with measure() as measurement:
            list(Article.objects.all())
            list(Article.objects.all())
        assert measurement.query_count == 2
