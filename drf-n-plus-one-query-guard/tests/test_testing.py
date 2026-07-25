"""Tests for :mod:`drf_n_plus_one_query_guard.testing`."""

from __future__ import annotations

import pytest

from drf_n_plus_one_query_guard.testing import assert_no_n_plus_one
from tests.test_app.models import Article

pytestmark = pytest.mark.django_db


class TestAssertNoNPlusOne:
    def test_passes_when_query_pattern_is_fine(self, make_article) -> None:
        with assert_no_n_plus_one():
            list(Article.objects.select_related("author").all())

    def test_raises_assertion_error_on_n_plus_one(self, several_articles) -> None:
        with pytest.raises(AssertionError, match="Suspected N\\+1"), assert_no_n_plus_one():
            for article in Article.objects.all():
                _ = article.author.name

    def test_default_threshold_is_two(self, several_articles) -> None:
        with pytest.raises(AssertionError), assert_no_n_plus_one():
            for article in Article.objects.all():
                _ = article.author.name

    def test_custom_threshold_is_respected(self, several_articles) -> None:
        # 5 articles -> 5 repeated author lookups; a threshold above that
        # should not trip the assertion.
        with assert_no_n_plus_one(threshold=10):
            for article in Article.objects.all():
                _ = article.author.name

    def test_ignore_patterns_suppress_matching_fingerprints(self, several_articles) -> None:
        with assert_no_n_plus_one(ignore_patterns=["test_app_author"]):
            for article in Article.objects.all():
                _ = article.author.name

    def test_violations_available_after_a_failed_assertion(self, several_articles) -> None:
        assertion = assert_no_n_plus_one()
        with pytest.raises(AssertionError), assertion:
            for article in Article.objects.all():
                _ = article.author.name
        assert len(assertion.violations) == 1

    def test_a_real_test_failure_is_not_masked(self, several_articles) -> None:
        with pytest.raises(ValueError, match="boom"), assert_no_n_plus_one():
            for article in Article.objects.all():
                _ = article.author.name
            raise ValueError("boom")
