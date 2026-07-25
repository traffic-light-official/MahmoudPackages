"""Tests for the 9 concrete generic views in :mod:`drf_async.generics`.

Exercised directly via ``AsyncRequestFactory`` + ``as_view()``, without
a full URL conf - each concrete view is a one-line delegation to an
already-integration-tested mixin action, so these tests only need to
prove the HTTP-verb-to-action wiring itself, not re-prove the mixins.

Every article title in this file is unique across the whole file, even
across unrelated test classes - ``ArticleSerializer.title`` carries a
``UniqueValidator``, and pytest-django does not fully isolate the
database between ``async def`` tests the way it does for sync ones (a
row committed by one async test can still be visible to the next one in
the same run) - see ``docs/testing.md`` for the full explanation. Reused
titles like ``"Updated"`` across two different test classes silently
collide with a *different* row's data, not this package's own code.
"""

from __future__ import annotations

import json

import pytest
from django.test import AsyncRequestFactory
from rest_framework.exceptions import APIException
from rest_framework.permissions import AllowAny, BasePermission

from drf_async.generics import (
    AsyncCreateAPIView,
    AsyncDestroyAPIView,
    AsyncListAPIView,
    AsyncListCreateAPIView,
    AsyncRetrieveAPIView,
    AsyncRetrieveDestroyAPIView,
    AsyncRetrieveUpdateAPIView,
    AsyncRetrieveUpdateDestroyAPIView,
    AsyncUpdateAPIView,
)
from tests.test_app.models import Article
from tests.test_app.serializers import ArticleSerializer

pytestmark = pytest.mark.django_db(transaction=True)

factory = AsyncRequestFactory()


def _json_body(data: object) -> dict[str, str]:
    """``RequestFactory.put()``/``.patch()`` need an explicit content type - unlike
    ``.post()``, they don't auto-encode a dict as multipart."""
    return {"data": json.dumps(data), "content_type": "application/json"}


def _view(base: type, **attrs: object) -> type:
    return type(
        "TestView",
        (base,),
        {
            "permission_classes": [AllowAny],
            "serializer_class": ArticleSerializer,
            "queryset": Article.objects.all(),
            **attrs,
        },
    )


class TestAsyncListAPIView:
    async def test_lists_articles(self, make_article) -> None:
        await make_article(title="ListAPIView Article")
        request = factory.get("/x/")
        response = await _view(AsyncListAPIView).as_view()(request)
        assert response.status_code == 200
        assert len(response.data) == 1


class TestAsyncCreateAPIView:
    async def test_creates_an_article(self, make_author) -> None:
        author = await make_author()
        request = factory.post("/x/", data={"title": "CreateAPIView New", "author": author.pk})
        response = await _view(AsyncCreateAPIView).as_view()(request)
        assert response.status_code == 201


class TestAsyncRetrieveAPIView:
    async def test_retrieves_an_article(self, make_article) -> None:
        article = await make_article(title="RetrieveAPIView Article")
        request = factory.get(f"/x/{article.pk}/")
        response = await _view(AsyncRetrieveAPIView).as_view()(request, pk=article.pk)
        assert response.status_code == 200
        assert response.data["title"] == "RetrieveAPIView Article"


class TestAsyncUpdateAPIView:
    async def test_put_updates(self, make_article) -> None:
        article = await make_article(title="UpdateAPIView Original (put)")
        request = factory.put(
            f"/x/{article.pk}/",
            **_json_body({"title": "UpdateAPIView Updated (put)", "author": article.author_id}),
        )
        response = await _view(AsyncUpdateAPIView).as_view()(request, pk=article.pk)
        assert response.status_code == 200
        assert response.data["title"] == "UpdateAPIView Updated (put)"

    async def test_patch_partial_updates(self, make_article) -> None:
        article = await make_article(title="UpdateAPIView Original (patch)")
        request = factory.patch(
            f"/x/{article.pk}/", **_json_body({"title": "UpdateAPIView Patched"})
        )
        response = await _view(AsyncUpdateAPIView).as_view()(request, pk=article.pk)
        assert response.status_code == 200
        assert response.data["title"] == "UpdateAPIView Patched"


class TestAsyncDestroyAPIView:
    async def test_deletes_an_article(self, make_article) -> None:
        article = await make_article(title="DestroyAPIView Delete Me")
        request = factory.delete(f"/x/{article.pk}/")
        response = await _view(AsyncDestroyAPIView).as_view()(request, pk=article.pk)
        assert response.status_code == 204


class TestAsyncListCreateAPIView:
    async def test_get_lists(self, make_article) -> None:
        await make_article(title="ListCreateAPIView Listed")
        request = factory.get("/x/")
        response = await _view(AsyncListCreateAPIView).as_view()(request)
        assert response.status_code == 200

    async def test_post_creates(self, make_author) -> None:
        author = await make_author()
        request = factory.post(
            "/x/", **_json_body({"title": "ListCreateAPIView New", "author": author.pk})
        )
        response = await _view(AsyncListCreateAPIView).as_view()(request)
        assert response.status_code == 201


class TestAsyncRetrieveUpdateAPIView:
    async def test_get_retrieves(self, make_article) -> None:
        article = await make_article(title="RetrieveUpdateAPIView Get")
        request = factory.get(f"/x/{article.pk}/")
        response = await _view(AsyncRetrieveUpdateAPIView).as_view()(request, pk=article.pk)
        assert response.status_code == 200

    async def test_put_updates(self, make_article) -> None:
        article = await make_article(title="RetrieveUpdateAPIView Original (put)")
        request = factory.put(
            f"/x/{article.pk}/",
            **_json_body(
                {"title": "RetrieveUpdateAPIView Updated (put)", "author": article.author_id}
            ),
        )
        response = await _view(AsyncRetrieveUpdateAPIView).as_view()(request, pk=article.pk)
        assert response.status_code == 200

    async def test_patch_partial_updates(self, make_article) -> None:
        article = await make_article(title="RetrieveUpdateAPIView Original (patch)")
        request = factory.patch(
            f"/x/{article.pk}/", **_json_body({"title": "RetrieveUpdateAPIView Patched"})
        )
        response = await _view(AsyncRetrieveUpdateAPIView).as_view()(request, pk=article.pk)
        assert response.status_code == 200


class TestAsyncRetrieveDestroyAPIView:
    async def test_get_retrieves(self, make_article) -> None:
        article = await make_article(title="RetrieveDestroyAPIView Get")
        request = factory.get(f"/x/{article.pk}/")
        response = await _view(AsyncRetrieveDestroyAPIView).as_view()(request, pk=article.pk)
        assert response.status_code == 200

    async def test_delete_destroys(self, make_article) -> None:
        article = await make_article(title="RetrieveDestroyAPIView Delete Me")
        request = factory.delete(f"/x/{article.pk}/")
        response = await _view(AsyncRetrieveDestroyAPIView).as_view()(request, pk=article.pk)
        assert response.status_code == 204


class TestAsyncRetrieveUpdateDestroyAPIView:
    async def test_get_retrieves(self, make_article) -> None:
        article = await make_article(title="RetrieveUpdateDestroyAPIView Get")
        request = factory.get(f"/x/{article.pk}/")
        response = await _view(AsyncRetrieveUpdateDestroyAPIView).as_view()(request, pk=article.pk)
        assert response.status_code == 200

    async def test_put_updates(self, make_article) -> None:
        article = await make_article(title="RetrieveUpdateDestroyAPIView Original (put)")
        request = factory.put(
            f"/x/{article.pk}/",
            **_json_body(
                {
                    "title": "RetrieveUpdateDestroyAPIView Updated (put)",
                    "author": article.author_id,
                }
            ),
        )
        response = await _view(AsyncRetrieveUpdateDestroyAPIView).as_view()(request, pk=article.pk)
        assert response.status_code == 200

    async def test_patch_partial_updates(self, make_article) -> None:
        article = await make_article(title="RetrieveUpdateDestroyAPIView Original (patch)")
        request = factory.patch(
            f"/x/{article.pk}/", **_json_body({"title": "RetrieveUpdateDestroyAPIView Patched"})
        )
        response = await _view(AsyncRetrieveUpdateDestroyAPIView).as_view()(request, pk=article.pk)
        assert response.status_code == 200

    async def test_delete_destroys(self, make_article) -> None:
        article = await make_article(title="RetrieveUpdateDestroyAPIView Delete Me")
        request = factory.delete(f"/x/{article.pk}/")
        response = await _view(AsyncRetrieveUpdateDestroyAPIView).as_view()(request, pk=article.pk)
        assert response.status_code == 204


class _DenyObjectPermission(BasePermission):
    """Allows the request itself but denies every object-level check."""

    def has_object_permission(self, request: object, view: object, obj: object) -> bool:
        return False


class TestAsyncObjectPermissionDenied:
    async def test_denied_object_permission_raises_403(self, make_article) -> None:
        article = await make_article(title="ObjectPermissionDenied Article")
        request = factory.get(f"/x/{article.pk}/")
        view = _view(AsyncRetrieveAPIView, permission_classes=[_DenyObjectPermission])
        response = await view.as_view()(request, pk=article.pk)
        assert response.status_code == 403


class TestAsyncGetObjectNotFound:
    async def test_missing_object_raises_http404(self) -> None:
        request = factory.get("/x/999999/")
        response = await _view(AsyncRetrieveAPIView).as_view()(request, pk=999999)
        assert response.status_code == 404

    async def test_malformed_lookup_value_raises_http404(self) -> None:
        request = factory.get("/x/not-a-number/")
        response = await _view(AsyncRetrieveAPIView).as_view()(request, pk="not-a-number")
        assert response.status_code == 404

    async def test_missing_lookup_kwarg_raises_assertion_error(self) -> None:
        request = factory.get("/x/")
        with pytest.raises(AssertionError, match="URL conf"):
            await _view(AsyncRetrieveAPIView).as_view()(request)


class TestGetPaginatedResponseWithoutPaginator:
    def test_raises_api_exception_when_unpaginated(self) -> None:
        view = _view(AsyncRetrieveAPIView, pagination_class=None)()
        with pytest.raises(APIException, match="no `pagination_class`"):
            view.get_paginated_response([])
