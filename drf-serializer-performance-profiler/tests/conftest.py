"""Shared pytest fixtures for the test suite."""

from __future__ import annotations

from collections.abc import Callable

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from tests.test_app.models import Article, Author, Comment


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def make_user(db: None) -> Callable[..., User]:
    counter = iter(range(1, 10_000))

    def _make(*, is_staff: bool = False) -> User:
        return User.objects.create_user(username=f"user{next(counter)}", is_staff=is_staff)

    return _make


@pytest.fixture
def make_author(db: None) -> Callable[..., Author]:
    def _make(name: str = "Ada Lovelace") -> Author:
        return Author.objects.create(name=name)

    return _make


@pytest.fixture
def make_article(db: None, make_author: Callable[..., Author]) -> Callable[..., Article]:
    def _make(
        title: str = "An Article", author: Author | None = None, comment_count: int = 0
    ) -> Article:
        resolved_author = author or make_author()
        article = Article.objects.create(title=title, author=resolved_author)
        for i in range(comment_count):
            Comment.objects.create(article=article, body=f"Comment {i}")
        return article

    return _make
