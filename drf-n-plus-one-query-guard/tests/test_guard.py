"""Tests for :mod:`drf_n_plus_one_query_guard.guard`."""

from __future__ import annotations

import logging

import pytest
from django.test import override_settings

from drf_n_plus_one_query_guard.exceptions import NPlusOneDetectedError
from drf_n_plus_one_query_guard.guard import NPlusOneGuard
from tests.test_app.models import Article

pytestmark = pytest.mark.django_db


class TestNPlusOneGuardDefaults:
    def test_uses_settings_by_default(self) -> None:
        with override_settings(N_PLUS_ONE_GUARD={"THRESHOLD": 3, "MODE": "report"}):
            guard = NPlusOneGuard()
        assert guard.threshold == 3
        assert guard.mode == "report"

    def test_explicit_arguments_override_settings(self) -> None:
        with override_settings(N_PLUS_ONE_GUARD={"THRESHOLD": 3, "MODE": "report"}):
            guard = NPlusOneGuard(threshold=10, mode="warn")
        assert guard.threshold == 10
        assert guard.mode == "warn"


class TestNPlusOneGuardReportMode:
    def test_no_violations_when_query_pattern_is_fine(self, make_article) -> None:
        with NPlusOneGuard(mode="report") as guard:
            list(Article.objects.select_related("author").all())
        assert guard.violations == []

    def test_violations_populated_but_nothing_raised(self, several_articles) -> None:
        with NPlusOneGuard(mode="report", threshold=2) as guard:
            for article in Article.objects.all():
                _ = article.author.name
        assert len(guard.violations) == 1


class TestNPlusOneGuardRaiseMode:
    def test_raises_when_violation_found(self, several_articles) -> None:
        with pytest.raises(NPlusOneDetectedError), NPlusOneGuard(mode="raise", threshold=2):
            for article in Article.objects.all():
                _ = article.author.name

    def test_does_not_raise_when_no_violation(self, make_article) -> None:
        with NPlusOneGuard(mode="raise", threshold=2):
            list(Article.objects.select_related("author").all())

    def test_a_real_exception_from_the_body_is_not_masked(self, several_articles) -> None:
        with pytest.raises(ValueError, match="boom"), NPlusOneGuard(mode="raise", threshold=2):
            for article in Article.objects.all():
                _ = article.author.name
            raise ValueError("boom")


class TestNPlusOneGuardWarnMode:
    def test_logs_a_warning_per_violation(
        self, caplog: pytest.LogCaptureFixture, several_articles
    ) -> None:
        with (
            caplog.at_level(logging.WARNING, logger="drf_n_plus_one_query_guard"),
            NPlusOneGuard(mode="warn", threshold=2),
        ):
            for article in Article.objects.all():
                _ = article.author.name

        assert any("Suspected N+1" in record.message for record in caplog.records)

    def test_no_log_when_no_violation(self, caplog: pytest.LogCaptureFixture, make_article) -> None:
        with (
            caplog.at_level(logging.WARNING, logger="drf_n_plus_one_query_guard"),
            NPlusOneGuard(mode="warn", threshold=2),
        ):
            list(Article.objects.select_related("author").all())

        assert caplog.records == []


class TestNPlusOneGuardIgnorePatterns:
    def test_configured_ignore_pattern_suppresses_violation(self, several_articles) -> None:
        with (
            override_settings(
                N_PLUS_ONE_GUARD={"IGNORE_PATTERNS": ["test_app_author"], "MODE": "report"}
            ),
            NPlusOneGuard(threshold=2) as guard,
        ):
            for article in Article.objects.all():
                _ = article.author.name

        assert guard.violations == []
