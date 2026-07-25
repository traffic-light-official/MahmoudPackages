"""Tests for :mod:`drf_n_plus_one_query_guard.tracker`."""

from __future__ import annotations

import re
from collections.abc import Callable

import pytest

from drf_n_plus_one_query_guard.tracker import QueryTracker
from tests.test_app.models import Article, Author

pytestmark = pytest.mark.django_db


class TestQueryTrackerCapturesEvents:
    def test_records_one_event_per_executed_query(self) -> None:
        with QueryTracker() as tracker:
            list(Author.objects.all())
            list(Author.objects.all())

        assert len(tracker.events) == 2

    def test_records_nothing_outside_the_context(self) -> None:
        tracker = QueryTracker()
        list(Author.objects.all())
        assert tracker.events == []

    def test_event_fingerprint_is_normalized(self) -> None:
        with QueryTracker() as tracker:
            list(Author.objects.all())

        assert "\n" not in tracker.events[0].fingerprint

    def test_event_records_the_database_alias(self) -> None:
        with QueryTracker() as tracker:
            list(Author.objects.all())

        assert tracker.events[0].alias == "default"

    def test_event_call_site_points_at_this_test_file(self) -> None:
        with QueryTracker() as tracker:
            list(Author.objects.all())

        assert "test_tracker.py" in tracker.events[0].call_site


class TestQueryTrackerViolations:
    def test_no_violations_when_nothing_repeats(self, make_author: Callable[..., Author]) -> None:
        make_author(name="Ada")
        with QueryTracker() as tracker:
            list(Author.objects.all())

        assert tracker.violations(threshold=2) == []

    def test_the_classic_n_plus_one_is_detected(self, several_articles: list[Article]) -> None:
        with QueryTracker() as tracker:
            for article in Article.objects.all():
                _ = article.author.name  # one extra query per row, unoptimized

        violations = tracker.violations(threshold=2)

        assert len(violations) == 1
        assert violations[0].count == 5

    def test_select_related_eliminates_the_violation(self, several_articles: list[Article]) -> None:
        with QueryTracker() as tracker:
            for article in Article.objects.select_related("author"):
                _ = article.author.name

        assert tracker.violations(threshold=2) == []

    def test_violation_reports_sample_sql_and_call_site(
        self, several_articles: list[Article]
    ) -> None:
        with QueryTracker() as tracker:
            for article in Article.objects.all():
                _ = article.author.name

        (violation,) = tracker.violations(threshold=2)
        assert "test_app_author" in violation.sample_sql
        assert "test_tracker.py" in violation.call_site

    def test_ignore_patterns_exclude_matching_fingerprints(
        self, several_articles: list[Article]
    ) -> None:
        with QueryTracker() as tracker:
            for article in Article.objects.all():
                _ = article.author.name

        pattern = re.compile(r"test_app_author")
        assert tracker.violations(threshold=2, ignore_patterns=[pattern]) == []

    def test_violations_below_threshold_are_not_reported(
        self, several_articles: list[Article]
    ) -> None:
        with QueryTracker() as tracker:
            for article in Article.objects.all():
                _ = article.author.name

        assert tracker.violations(threshold=10) == []

    def test_call_sites_lists_every_distinct_location(
        self, several_articles: list[Article]
    ) -> None:
        def access_author(article: Article) -> str:
            return article.author.name

        with QueryTracker() as tracker:
            for article in Article.objects.all():
                access_author(article)

        (violation,) = tracker.violations(threshold=2)
        assert len(violation.call_sites) >= 1
