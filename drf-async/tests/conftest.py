"""Shared fixtures for the drf-async test suite.

``make_author``/``make_article`` are async factories, not plain sync
ones: calling a sync, database-touching function directly from inside
an ``async def test_...`` body raises ``SynchronousOnlyOperation``,
since by that point the test is already running inside pytest-asyncio's
event loop - unlike a plain fixture *value* (resolved before the async
test body starts), a factory *called from within* the test body needs
its own ``sync_to_async`` bridge, same as this package's own views need
for exactly the same reason.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

import pytest
from asgiref.sync import sync_to_async
from django.core.cache import cache
from django.test import AsyncClient

from tests.test_app.models import Article, Author


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    """Throttle state lives in Django's cache, which pytest-django never resets."""
    cache.clear()


@pytest.fixture
def api_client() -> AsyncClient:
    """Django's own async-capable test client (stable since Django 4.2)."""
    return AsyncClient()


@pytest.fixture
def make_author(db: None) -> Callable[..., Awaitable[Author]]:
    async def _make(name: str = "Ada Lovelace") -> Author:
        return await sync_to_async(Author.objects.create, thread_sensitive=True)(name=name)

    return _make


@pytest.fixture
def make_article(
    db: None, make_author: Callable[..., Awaitable[Author]]
) -> Callable[..., Awaitable[Article]]:
    async def _make(title: str = "An Article", author: Author | None = None) -> Article:
        resolved_author = author or await make_author()
        return await sync_to_async(Article.objects.create, thread_sensitive=True)(
            title=title, author=resolved_author
        )

    return _make
