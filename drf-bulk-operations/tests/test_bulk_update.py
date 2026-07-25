"""Integration tests for ``bulk_update``/``bulk_partial_update``."""

from __future__ import annotations

import pytest
from django.test import override_settings
from rest_framework import status

pytestmark = pytest.mark.django_db


class TestBulkUpdateAtomicDefault:
    def test_all_valid_items_are_updated(self, api_client, make_article) -> None:
        first = make_article(title="Update Me A")
        second = make_article(title="Update Me B", author=first.author)
        response = api_client.put(
            "/articles/bulk-update/",
            [
                {"id": first.pk, "title": "Updated A", "author": first.author_id},
                {"id": second.pk, "title": "Updated B", "author": second.author_id},
            ],
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert [item["title"] for item in response.data] == ["Updated A", "Updated B"]
        first.refresh_from_db()
        assert first.title == "Updated A"

    def test_missing_lookup_field_aborts_the_whole_batch(self, api_client, make_article) -> None:
        article = make_article(title="Has No Id In Payload")
        response = api_client.put(
            "/articles/bulk-update/",
            [{"title": "New Title", "author": article.author_id}],
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "id" in response.data[0]["detail"]
        article.refresh_from_db()
        assert article.title == "Has No Id In Payload"

    def test_nonexistent_id_aborts_the_whole_batch(self, api_client, make_article) -> None:
        article = make_article(title="Untouched")
        response = api_client.put(
            "/articles/bulk-update/",
            [
                {"id": article.pk, "title": "Should Not Apply", "author": article.author_id},
                {"id": 999999, "title": "Ghost", "author": article.author_id},
            ],
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "No object found" in response.data[1]["detail"]
        article.refresh_from_db()
        assert article.title == "Untouched"


class TestBulkPartialUpdate:
    def test_partial_update_only_changes_submitted_fields(self, api_client, make_article) -> None:
        article = make_article(title="Original Title", published=False)
        response = api_client.patch(
            "/articles/bulk-partial-update/",
            [{"id": article.pk, "published": True}],
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data[0]["title"] == "Original Title"
        assert response.data[0]["published"] is True


class TestBulkUpdateNonAtomic:
    def test_mixed_batch_returns_207_and_applies_the_valid_item(
        self, api_client, make_article
    ) -> None:
        first = make_article(title="Non-Atomic Update Valid")
        with override_settings(BULK_OPERATIONS={"ATOMIC": False}):
            response = api_client.put(
                "/articles/bulk-update/",
                [
                    {"id": first.pk, "title": "Now Updated", "author": first.author_id},
                    {"id": 999999, "title": "Ghost", "author": first.author_id},
                ],
                format="json",
            )
        assert response.status_code == status.HTTP_207_MULTI_STATUS
        assert response.data[0]["status"] == "success"
        assert response.data[1]["status"] == "error"
        first.refresh_from_db()
        assert first.title == "Now Updated"

    def test_invalid_item_data_is_reported_per_item(self, api_client, make_article) -> None:
        article = make_article(title="Non-Atomic Validation Survivor")
        with override_settings(BULK_OPERATIONS={"ATOMIC": False}):
            response = api_client.put(
                "/articles/bulk-update/",
                [{"id": article.pk, "title": "", "author": article.author_id}],
                format="json",
            )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "title" in response.data[0]["errors"]
        article.refresh_from_db()
        assert article.title == "Non-Atomic Validation Survivor"


class TestBulkUpdateObjectPermissionDenied:
    def test_denied_object_permission_aborts_with_403(self, make_article) -> None:
        from rest_framework.permissions import BasePermission
        from rest_framework.test import APIRequestFactory

        from drf_bulk_operations import BulkModelViewSet
        from tests.test_app.models import Article
        from tests.test_app.serializers import ArticleSerializer

        class _DenyObjectPermission(BasePermission):
            def has_object_permission(self, request: object, view: object, obj: object) -> bool:
                return False

        class _DeniedViewSet(BulkModelViewSet):
            permission_classes = [_DenyObjectPermission]
            serializer_class = ArticleSerializer
            queryset = Article.objects.all()

        article = make_article(title="Protected Article")
        factory = APIRequestFactory()
        request = factory.put(
            "/x/bulk-update/",
            [{"id": article.pk, "title": "Hacked", "author": article.author_id}],
            format="json",
        )
        view = _DeniedViewSet.as_view({"put": "bulk_update"})
        response = view(request)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        article.refresh_from_db()
        assert article.title == "Protected Article"
