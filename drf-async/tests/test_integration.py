"""End-to-end tests: real HTTP requests via ``django.test.AsyncClient``.

This is the file that actually proves the sync/async bridging is
correct - a mistake here typically manifests as
``SynchronousOnlyOperation`` at request time, not at import time or in
a type checker.
"""

from __future__ import annotations

import pytest
from django.contrib.auth.models import User
from django.test import AsyncClient

pytestmark = pytest.mark.django_db(transaction=True)


class TestPingView:
    async def test_returns_200(self, api_client: AsyncClient) -> None:
        response = await api_client.get("/ping/")
        assert response.status_code == 200
        assert response.json() == {"pong": True}

    async def test_unsupported_method_returns_405(self, api_client: AsyncClient) -> None:
        response = await api_client.put("/ping/")
        assert response.status_code == 405


class TestSyncPermission:
    async def test_anonymous_request_is_rejected(self, api_client: AsyncClient) -> None:
        response = await api_client.get("/sync-permission/")
        assert response.status_code == 403

    async def test_authenticated_request_is_allowed(self, api_client: AsyncClient) -> None:
        user = await User.objects.acreate(username="ada")
        await api_client.aforce_login(user)
        response = await api_client.get("/sync-permission/")
        assert response.status_code == 200
        assert response.json() == {"authenticated": True}


class TestAsyncPermission:
    async def test_denied_by_async_permission(self, api_client: AsyncClient) -> None:
        response = await api_client.get("/async-permission-denied/")
        assert response.status_code == 403
        assert "DenyAllAsyncPermission" in response.json()["detail"]

    async def test_allowed_by_async_permission(self, api_client: AsyncClient) -> None:
        response = await api_client.get("/async-permission-allowed/")
        assert response.status_code == 200
        assert response.json() == {"allowed": True}


class TestAsyncThrottle:
    async def test_first_request_succeeds(self, api_client: AsyncClient) -> None:
        response = await api_client.get("/throttled/")
        assert response.status_code == 200

    async def test_second_request_from_the_same_client_is_throttled(
        self, api_client: AsyncClient
    ) -> None:
        first = await api_client.get("/throttled/")
        second = await api_client.get("/throttled/")
        assert first.status_code == 200
        assert second.status_code == 429

    async def test_different_clients_are_throttled_independently(
        self, api_client: AsyncClient
    ) -> None:
        response_a = await api_client.get("/throttled/", headers={"X-Client-Id": "client-a"})
        response_b = await api_client.get("/throttled/", headers={"X-Client-Id": "client-b"})

        assert response_a.status_code == 200
        assert response_b.status_code == 200


class TestArticleViewSetList:
    async def test_empty_list(self, api_client: AsyncClient) -> None:
        response = await api_client.get("/articles/")
        assert response.status_code == 200
        assert response.json()["results"] == []

    async def test_lists_articles_paginated(self, make_article) -> None:
        await make_article(title="One")
        await make_article(title="Two")
        await make_article(title="Three")

        client = AsyncClient()
        response = await client.get("/articles/")

        assert response.status_code == 200
        body = response.json()
        assert body["count"] == 3
        assert len(body["results"]) == 2  # page_size=2
        assert body["next"] is not None


class TestArticleViewSetCreate:
    async def test_creates_an_article(self, make_author) -> None:
        author = await make_author(name="Grace Hopper")
        client = AsyncClient()

        response = await client.post(
            "/articles/",
            data={"title": "New Article", "author": author.pk},
            content_type="application/json",
        )

        assert response.status_code == 201
        assert response.json()["title"] == "New Article"

    async def test_unique_title_validator_rejects_a_duplicate(
        self, make_article, make_author
    ) -> None:
        await make_article(title="Duplicate Title")
        author = await make_author(name="Someone Else")
        client = AsyncClient()

        response = await client.post(
            "/articles/",
            data={"title": "Duplicate Title", "author": author.pk},
            content_type="application/json",
        )

        assert response.status_code == 400
        assert "title" in response.json()


class TestArticleViewSetRetrieveUpdateDestroy:
    async def test_retrieves_an_article(self, make_article) -> None:
        article = await make_article(title="Retrieve Me")
        client = AsyncClient()

        response = await client.get(f"/articles/{article.pk}/")

        assert response.status_code == 200
        assert response.json()["title"] == "Retrieve Me"

    async def test_retrieving_a_missing_article_is_404(self, api_client: AsyncClient) -> None:
        response = await api_client.get("/articles/999999/")
        assert response.status_code == 404

    async def test_full_update(self, make_article) -> None:
        article = await make_article(title="Original")
        client = AsyncClient()

        response = await client.put(
            f"/articles/{article.pk}/",
            data={"title": "Updated", "author": article.author_id},
            content_type="application/json",
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Updated"

    async def test_partial_update(self, make_article) -> None:
        article = await make_article(title="Original")
        client = AsyncClient()

        response = await client.patch(
            f"/articles/{article.pk}/",
            data={"title": "Patched"},
            content_type="application/json",
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Patched"

    async def test_destroy(self, make_article) -> None:
        article = await make_article(title="Delete Me")
        client = AsyncClient()

        response = await client.delete(f"/articles/{article.pk}/")

        assert response.status_code == 204
        follow_up = await client.get(f"/articles/{article.pk}/")
        assert follow_up.status_code == 404
