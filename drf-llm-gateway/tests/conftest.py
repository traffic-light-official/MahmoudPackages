"""Shared pytest fixtures for the test suite."""

from __future__ import annotations

import pytest
from django.contrib.auth.models import User

from drf_llm_gateway.registry import default_registry
from tests.test_app.models import Article, Author, Tag


@pytest.fixture(autouse=True)
def _clean_registry_state() -> None:
    """Ensure test_app's module-level @expose_as_tool registrations exist.

    Importing tests.test_app.views (triggered by the fixtures/urls below)
    registers tools exactly once at import time; this fixture is a no-op
    placeholder ensuring the import has happened before each test runs.
    """
    import tests.test_app.views  # noqa: F401


@pytest.fixture
def author(db: None) -> Author:
    return Author.objects.create(name="Ada Lovelace", email="ada@example.com")


@pytest.fixture
def tag(db: None) -> Tag:
    return Tag.objects.create(label="django")


@pytest.fixture
def article(db: None, author: Author, tag: Tag) -> Article:
    article = Article.objects.create(title="Hello World", author=author)
    article.tags.add(tag)
    return article


@pytest.fixture
def user(db: None) -> User:
    return User.objects.create_user(username="alice", password="password123")


@pytest.fixture
def registry() -> object:
    return default_registry
