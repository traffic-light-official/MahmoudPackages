"""End-to-end HTTP tests through the DRF test client and URLconf."""

from __future__ import annotations

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from tests.test_app.models import Article

pytestmark = pytest.mark.django_db


@pytest.fixture
def client() -> APIClient:
    return APIClient()


class TestListEndpoint:
    def test_no_fields_param_returns_full_representation(
        self, client: APIClient, article: Article
    ) -> None:
        response = client.get("/articles/")
        assert response.status_code == status.HTTP_200_OK
        item = response.data["results"][0]
        assert "body" in item
        assert "author" in item

    def test_fields_param_narrows_response(self, client: APIClient, article: Article) -> None:
        response = client.get("/articles/?fields=title,author(name)")
        assert response.status_code == status.HTTP_200_OK
        item = response.data["results"][0]
        assert set(item) == {"title", "author", "id"}
        assert set(item["author"]) == {"name", "id"}

    def test_invalid_fields_param_returns_400(self, client: APIClient, article: Article) -> None:
        response = client.get("/articles/?fields=author(name")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "fields" in response.data

    def test_pagination_composes_with_field_filtering(
        self, client: APIClient, many_articles: list[Article]
    ) -> None:
        response = client.get("/articles/?fields=title&page_size=2")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2
        assert set(response.data["results"][0]) == {"title", "id"}
        assert "next" in response.data


class TestDetailEndpoint:
    def test_retrieve_honors_fields_param(self, client: APIClient, article: Article) -> None:
        response = client.get(f"/articles/{article.pk}/?fields=title")
        assert response.status_code == status.HTTP_200_OK
        assert set(response.data) == {"title", "id"}

    def test_retrieve_without_fields_param_is_unchanged(
        self, client: APIClient, article: Article
    ) -> None:
        response = client.get(f"/articles/{article.pk}/")
        assert response.status_code == status.HTTP_200_OK
        assert "comment_count" in response.data
        assert response.data["comment_count"] == 2


class TestBrowsableApi:
    def test_browsable_api_renders_without_error(self, client: APIClient, article: Article) -> None:
        response = client.get("/articles/?fields=title", HTTP_ACCEPT="text/html")
        assert response.status_code == status.HTTP_200_OK
        assert b"title" in response.content


class TestWriteOperationsUnaffected:
    def test_create_ignores_fields_param_entirely_by_default(
        self, client: APIClient, article: Article
    ) -> None:
        """POST is an unsafe method, so ``fields=`` must not narrow the
        writable field set (which would silently break input validation)
        nor the response representation - see the ``SAFE_METHODS_ONLY``
        setting."""
        payload = {
            "title": "New Article",
            "body": "Body text",
            "author_id": article.author_id,
        }
        response = client.post("/articles/?fields=title", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert "body" in response.data
        assert "comment_count" in response.data

    def test_create_without_fields_param_still_works(
        self, client: APIClient, article: Article
    ) -> None:
        payload = {
            "title": "Another Article",
            "body": "Body text",
            "author_id": article.author_id,
        }
        response = client.post("/articles/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "Another Article"
