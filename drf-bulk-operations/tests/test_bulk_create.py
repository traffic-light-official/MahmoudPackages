"""Integration tests for ``bulk_create``, via real HTTP requests through the router."""

from __future__ import annotations

import pytest
from django.test import override_settings
from rest_framework import status

pytestmark = pytest.mark.django_db


class TestBulkCreateAtomicDefault:
    def test_all_valid_items_are_created(self, api_client, make_author) -> None:
        author = make_author()
        response = api_client.post(
            "/articles/bulk/",
            [
                {"title": "Article A", "author": author.pk},
                {"title": "Article B", "author": author.pk},
            ],
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert [item["title"] for item in response.data] == ["Article A", "Article B"]

    def test_one_invalid_item_aborts_the_whole_batch(self, api_client, make_author) -> None:
        author = make_author()
        response = api_client.post(
            "/articles/bulk/",
            [
                {"title": "Valid Article", "author": author.pk},
                {"title": "", "author": author.pk},  # blank title is invalid
            ],
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data[0] == {}
        assert "title" in response.data[1]

        from tests.test_app.models import Article

        assert not Article.objects.filter(title="Valid Article").exists()

    def test_within_batch_duplicate_title_rolls_back_the_whole_batch(
        self, api_client, make_author
    ) -> None:
        # Neither item conflicts with an *existing* row, so both pass the
        # serializer's UniqueValidator - the collision only surfaces as a
        # real database-level IntegrityError while saving the second item,
        # inside the same outer transaction as the first item's insert.
        author = make_author()
        response = api_client.post(
            "/articles/bulk/",
            [
                {"title": "Same Title", "author": author.pk},
                {"title": "Same Title", "author": author.pk},
            ],
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "rolled back" in response.data["detail"]

        from tests.test_app.models import Article

        assert Article.objects.filter(title="Same Title").count() == 0

    def test_not_a_list_body_is_rejected(self, api_client, make_author) -> None:
        author = make_author()
        response = api_client.post(
            "/articles/bulk/", {"title": "Solo", "author": author.pk}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "list" in response.data["detail"]

    def test_batch_size_exceeded_is_rejected(self, api_client, make_author) -> None:
        author = make_author()
        with override_settings(BULK_OPERATIONS={"MAX_BATCH_SIZE": 2}):
            response = api_client.post(
                "/articles/bulk/",
                [{"title": f"Article {i}", "author": author.pk} for i in range(3)],
                format="json",
            )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "exceeds the maximum" in response.data["detail"]


class TestBulkCreateNonAtomic:
    def test_all_valid_returns_201_with_plain_list(self, api_client, make_author) -> None:
        author = make_author()
        with override_settings(BULK_OPERATIONS={"ATOMIC": False}):
            response = api_client.post(
                "/articles/bulk/",
                [
                    {"title": "Non-Atomic A", "author": author.pk},
                    {"title": "Non-Atomic B", "author": author.pk},
                ],
                format="json",
            )
        assert response.status_code == status.HTTP_201_CREATED
        assert [item["title"] for item in response.data] == ["Non-Atomic A", "Non-Atomic B"]

    def test_mixed_batch_returns_207_and_saves_the_valid_item(
        self, api_client, make_author
    ) -> None:
        author = make_author()
        with override_settings(BULK_OPERATIONS={"ATOMIC": False}):
            response = api_client.post(
                "/articles/bulk/",
                [
                    {"title": "Non-Atomic Valid", "author": author.pk},
                    {"title": "", "author": author.pk},
                ],
                format="json",
            )
        assert response.status_code == status.HTTP_207_MULTI_STATUS
        assert response.data[0]["status"] == "success"
        assert response.data[1]["status"] == "error"

        from tests.test_app.models import Article

        assert Article.objects.filter(title="Non-Atomic Valid").exists()

    def test_within_batch_duplicate_title_is_caught_as_a_validation_error(
        self, api_client, make_author
    ) -> None:
        # Unlike atomic mode, the first item is committed via its own
        # savepoint *before* the second item is validated - so the second
        # item's UniqueValidator sees the already-committed duplicate and
        # rejects it as a normal validation error, not a database error.
        author = make_author()
        with override_settings(BULK_OPERATIONS={"ATOMIC": False}):
            response = api_client.post(
                "/articles/bulk/",
                [
                    {"title": "Non-Atomic Dup", "author": author.pk},
                    {"title": "Non-Atomic Dup", "author": author.pk},
                ],
                format="json",
            )
        assert response.status_code == status.HTTP_207_MULTI_STATUS
        assert response.data[0]["status"] == "success"
        assert response.data[1]["status"] == "error"
        assert "title" in response.data[1]["errors"]

        from tests.test_app.models import Article

        assert Article.objects.filter(title="Non-Atomic Dup").count() == 1

    def test_all_invalid_returns_400(self, api_client, make_author) -> None:
        author = make_author()
        with override_settings(BULK_OPERATIONS={"ATOMIC": False}):
            response = api_client.post(
                "/articles/bulk/",
                [{"title": "", "author": author.pk}, {"title": "", "author": author.pk}],
                format="json",
            )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert all(item["status"] == "error" for item in response.data)
