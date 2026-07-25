"""Shared fixtures for the drf-n-plus-one-query-guard test suite."""

from __future__ import annotations

from collections.abc import Callable

import pytest
from rest_framework.test import APIClient

from tests.test_app.models import Article, Author


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def make_author(db: None) -> Callable[..., Author]:
    def _make(name: str = "Ada Lovelace") -> Author:
        return Author.objects.create(name=name)

    return _make


@pytest.fixture
def make_article(db: None, make_author: Callable[..., Author]) -> Callable[..., Article]:
    def _make(title: str = "An Article", author: Author | None = None) -> Article:
        return Article.objects.create(title=title, author=author or make_author())

    return _make


@pytest.fixture
def several_articles(
    make_author: Callable[..., Author], make_article: Callable[..., Article]
) -> list[Article]:
    """Five articles, each with its own author - the classic N+1 shape."""
    return [
        make_article(title=f"Article {i}", author=make_author(name=f"Author {i}")) for i in range(5)
    ]
