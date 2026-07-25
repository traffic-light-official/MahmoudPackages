"""Shared pytest fixtures for the test suite."""

from __future__ import annotations

from collections.abc import Callable

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from tests.test_app.models import Article


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def make_user(db: None) -> Callable[..., User]:
    counter = iter(range(1, 10_000))

    def _make(*, is_staff: bool = False, username: str | None = None) -> User:
        name = username or f"user{next(counter)}"
        return User.objects.create_user(username=name, password="password", is_staff=is_staff)

    return _make


@pytest.fixture
def make_article(db: None, make_user: Callable[..., User]) -> Callable[..., Article]:
    def _make(title: str = "An Article", owner: User | None = None) -> Article:
        resolved_owner = owner or make_user()
        return Article.objects.create(title=title, owner=resolved_owner)

    return _make
