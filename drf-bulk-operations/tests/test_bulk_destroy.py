"""Integration tests for ``bulk_destroy``."""

from __future__ import annotations

import pytest
from django.test import override_settings
from rest_framework import status

pytestmark = pytest.mark.django_db


class TestBulkDestroyAtomicDefault:
    def test_all_valid_ids_are_deleted(self, api_client, make_article) -> None:
        first = make_article(title="Delete Me A")
        second = make_article(title="Delete Me B", author=first.author)
        response = api_client.delete("/articles/bulk-delete/", [first.pk, second.pk], format="json")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        from tests.test_app.models import Article

        assert not Article.objects.filter(pk__in=[first.pk, second.pk]).exists()

    def test_one_nonexistent_id_aborts_the_whole_batch(self, api_client, make_article) -> None:
        article = make_article(title="Should Survive")
        response = api_client.delete("/articles/bulk-delete/", [article.pk, 999999], format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data[0] == {}
        assert "No object found" in response.data[1]["detail"]

        from tests.test_app.models import Article

        assert Article.objects.filter(pk=article.pk).exists()

    def test_not_a_list_body_is_rejected(self, api_client) -> None:
        response = api_client.delete("/articles/bulk-delete/", {"id": 1}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestBulkDestroyNonAtomic:
    def test_mixed_batch_returns_207_and_deletes_the_valid_one(
        self, api_client, make_article
    ) -> None:
        article = make_article(title="Non-Atomic Delete Me")
        with override_settings(BULK_OPERATIONS={"ATOMIC": False}):
            response = api_client.delete(
                "/articles/bulk-delete/", [article.pk, 999999], format="json"
            )
        assert response.status_code == status.HTTP_207_MULTI_STATUS
        assert response.data[0]["status"] == "success"
        assert response.data[1]["status"] == "error"

        from tests.test_app.models import Article

        assert not Article.objects.filter(pk=article.pk).exists()

    def test_all_valid_returns_204_with_no_body(self, api_client, make_article) -> None:
        article = make_article(title="Non-Atomic Full Success")
        with override_settings(BULK_OPERATIONS={"ATOMIC": False}):
            response = api_client.delete("/articles/bulk-delete/", [article.pk], format="json")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.data is None


class TestBulkDestroyObjectPermissionDenied:
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

        article = make_article(title="Protected From Delete")
        factory = APIRequestFactory()
        request = factory.delete("/x/bulk-delete/", [article.pk], format="json")
        view = _DeniedViewSet.as_view({"delete": "bulk_destroy"})
        response = view(request)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Article.objects.filter(pk=article.pk).exists()
