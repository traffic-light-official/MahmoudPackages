"""Shared pytest fixtures for the test suite."""

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
    def _make(title: str = "An Article", author: Author | None = None, **extra: object) -> Article:
        resolved_author = author or make_author()
        return Article.objects.create(title=title, author=resolved_author, **extra)

    return _make
