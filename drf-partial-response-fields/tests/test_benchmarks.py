"""Performance benchmarks.

These run under ``pytest-benchmark`` and are also exercised as plain
correctness assertions (query-count reduction) so that a missing/broken
optimization fails CI, not just a benchmark report. Run
``pytest --benchmark-only`` to see timing output.
"""

from __future__ import annotations

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from drf_partial_response_fields.constants import CONTEXT_KEY
from drf_partial_response_fields.optimizer import optimize_queryset
from drf_partial_response_fields.parser import parse_fields
from tests.test_app.models import Article
from tests.test_app.serializers import ArticleSerializer

pytestmark = [pytest.mark.django_db, pytest.mark.benchmark]

COMPLEX_FIELDS = (
    "id,title,author(name,email,profile(display_name)),tags(label),comments(author_name,text)"
)


class TestParserPerformance:
    def test_parsing_complex_expression_is_fast(self, benchmark: object) -> None:
        result = benchmark(parse_fields, COMPLEX_FIELDS)  # type: ignore[operator]
        assert result.mode == "include"

    def test_parsing_scales_reasonably_with_field_count(self, benchmark: object) -> None:
        raw = ",".join(f"field_{i}" for i in range(200))
        result = benchmark(parse_fields, raw, max_length=10_000)  # type: ignore[operator]
        assert len(result.includes) == 200


class TestOptimizerPerformance:
    def test_optimize_queryset_overhead_is_small(self, benchmark: object, article: Article) -> None:
        tree = parse_fields(COMPLEX_FIELDS)

        def _run() -> object:
            return optimize_queryset(Article.objects.all(), ArticleSerializer, tree)

        benchmark(_run)  # type: ignore[operator]


class TestQueryCountBenchmark:
    """Documents the concrete query-count reduction claimed in the README."""

    def test_query_count_for_50_articles_stays_constant(self, author: object, tags: list) -> None:
        articles = [Article(title=f"A{i}", author=author) for i in range(50)]
        Article.objects.bulk_create(articles)
        for a in Article.objects.all():
            a.tags.set(tags[:1])

        tree = parse_fields("title,author(name),tags(label)")
        qs = optimize_queryset(Article.objects.all(), ArticleSerializer, tree)
        serializer = ArticleSerializer(qs, many=True, context={CONTEXT_KEY: tree})

        with CaptureQueriesContext(connection) as ctx:
            _ = serializer.data

        # 1 query for articles (with author joined) + 1 prefetch for tags,
        # independent of the number of articles.
        assert len(ctx.captured_queries) == 2
