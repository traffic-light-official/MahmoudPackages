"""Tests for the ``except DatabaseError`` branches in every bulk mixin.

``bulk_create``'s within-batch-duplicate-title scenario (see
``test_bulk_create.py``) already exercises the atomic create rollback
path with a *real*, un-forced ``IntegrityError``. The other five
database-error branches (non-atomic create, atomic/non-atomic update,
atomic/non-atomic destroy) have no equally natural trigger, so this
file uses a small ``perform_*``-overriding viewset that raises a real
``django.db.IntegrityError`` deterministically for one sentinel value -
the same technique real projects use to test "what if the database
itself rejects this" without depending on a race condition.
"""

from __future__ import annotations

import json

import pytest
from django.db import IntegrityError
from django.test import override_settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.test import APIRequestFactory

from drf_bulk_operations import BulkModelViewSet
from tests.test_app.models import Article
from tests.test_app.serializers import ArticleSerializer

pytestmark = pytest.mark.django_db

factory = APIRequestFactory()

_SENTINEL_TITLE = "trigger-db-error"


class _FlakySaveViewSet(BulkModelViewSet):
    """Fails to save/delete any item whose title is the sentinel value."""

    permission_classes = [AllowAny]
    serializer_class = ArticleSerializer
    queryset = Article.objects.all()

    def perform_create(self, serializer):  # type: ignore[override]
        if serializer.validated_data.get("title") == _SENTINEL_TITLE:
            raise IntegrityError("simulated create failure")
        serializer.save()

    def perform_update(self, serializer):  # type: ignore[override]
        if serializer.validated_data.get("title") == _SENTINEL_TITLE:
            raise IntegrityError("simulated update failure")
        serializer.save()

    def perform_destroy(self, instance):  # type: ignore[override]
        if instance.title == _SENTINEL_TITLE:
            raise IntegrityError("simulated destroy failure")
        instance.delete()


class TestBulkCreateDatabaseError:
    def test_non_atomic_failure_is_reported_per_item(self, make_author) -> None:
        author = make_author()
        request = factory.post(
            "/x/bulk/",
            [
                {"title": "Survives Create", "author": author.pk},
                {"title": _SENTINEL_TITLE, "author": author.pk},
            ],
            format="json",
        )
        with override_settings(BULK_OPERATIONS={"ATOMIC": False}):
            response = _FlakySaveViewSet.as_view({"post": "bulk_create"})(request)

        assert response.status_code == status.HTTP_207_MULTI_STATUS
        assert response.data[0]["status"] == "success"
        assert response.data[1]["status"] == "error"
        assert Article.objects.filter(title="Survives Create").exists()

    def test_atomic_failure_rolls_back_the_whole_batch(self, make_author) -> None:
        author = make_author()
        request = factory.post(
            "/x/bulk/",
            [
                {"title": "Should Roll Back", "author": author.pk},
                {"title": _SENTINEL_TITLE, "author": author.pk},
            ],
            format="json",
        )
        response = _FlakySaveViewSet.as_view({"post": "bulk_create"})(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "rolled back" in response.data["detail"]
        assert not Article.objects.filter(title="Should Roll Back").exists()


class TestBulkUpdateDatabaseError:
    def test_non_atomic_failure_is_reported_per_item(self, make_article) -> None:
        survivor = make_article(title="Update Survivor")
        victim = make_article(title="Update Victim", author=survivor.author)
        request = factory.put(
            "/x/bulk-update/",
            json.dumps(
                [
                    {"id": survivor.pk, "title": "Updated Survivor", "author": survivor.author_id},
                    {"id": victim.pk, "title": _SENTINEL_TITLE, "author": victim.author_id},
                ]
            ),
            content_type="application/json",
        )
        with override_settings(BULK_OPERATIONS={"ATOMIC": False}):
            response = _FlakySaveViewSet.as_view({"put": "bulk_update"})(request)

        assert response.status_code == status.HTTP_207_MULTI_STATUS
        survivor.refresh_from_db()
        victim.refresh_from_db()
        assert survivor.title == "Updated Survivor"
        assert victim.title == "Update Victim"

    def test_atomic_failure_rolls_back_the_whole_batch(self, make_article) -> None:
        survivor = make_article(title="Atomic Update Survivor")
        victim = make_article(title="Atomic Update Victim", author=survivor.author)
        request = factory.put(
            "/x/bulk-update/",
            json.dumps(
                [
                    {
                        "id": survivor.pk,
                        "title": "Should Not Apply",
                        "author": survivor.author_id,
                    },
                    {"id": victim.pk, "title": _SENTINEL_TITLE, "author": victim.author_id},
                ]
            ),
            content_type="application/json",
        )
        response = _FlakySaveViewSet.as_view({"put": "bulk_update"})(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "rolled back" in response.data["detail"]
        survivor.refresh_from_db()
        assert survivor.title == "Atomic Update Survivor"


class TestBulkDestroyDatabaseError:
    def test_non_atomic_failure_is_reported_per_item(self, make_article) -> None:
        survivor = make_article(title="Destroy Survivor")
        victim = make_article(title=_SENTINEL_TITLE, author=survivor.author)
        request = factory.delete(
            "/x/bulk-delete/", json.dumps([survivor.pk, victim.pk]), content_type="application/json"
        )
        with override_settings(BULK_OPERATIONS={"ATOMIC": False}):
            response = _FlakySaveViewSet.as_view({"delete": "bulk_destroy"})(request)

        assert response.status_code == status.HTTP_207_MULTI_STATUS
        assert not Article.objects.filter(pk=survivor.pk).exists()
        assert Article.objects.filter(pk=victim.pk).exists()

    def test_atomic_failure_rolls_back_the_whole_batch(self, make_article) -> None:
        survivor = make_article(title="Atomic Destroy Survivor")
        victim = make_article(title=_SENTINEL_TITLE, author=survivor.author)
        request = factory.delete(
            "/x/bulk-delete/", json.dumps([survivor.pk, victim.pk]), content_type="application/json"
        )
        response = _FlakySaveViewSet.as_view({"delete": "bulk_destroy"})(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "rolled back" in response.data["detail"]
        assert Article.objects.filter(pk=survivor.pk).exists()
