"""Example: bulk create, update, partial update, and delete, in both modes.

Run with:

    python -m examples.blog.example
"""

from __future__ import annotations

import json

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=False,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "rest_framework",
            "examples.blog",
        ],
        USE_TZ=True,
    )
    django.setup()

from django.test import override_settings
from django.test.runner import DiscoverRunner
from rest_framework.test import APIRequestFactory

from examples.blog.models import Article, Author
from examples.blog.views import ArticleViewSet

factory = APIRequestFactory()


def _post(path: str, data: object) -> None:
    request = factory.post(path, json.dumps(data), content_type="application/json")
    response = ArticleViewSet.as_view({"post": "bulk_create"})(request)
    print(f"  POST {path} -> {response.status_code} {response.data}")


def _put(path: str, data: object) -> None:
    request = factory.put(path, json.dumps(data), content_type="application/json")
    response = ArticleViewSet.as_view({"put": "bulk_update"})(request)
    print(f"  PUT {path} -> {response.status_code} {response.data}")


def _patch(path: str, data: object) -> None:
    request = factory.patch(path, json.dumps(data), content_type="application/json")
    response = ArticleViewSet.as_view({"patch": "bulk_partial_update"})(request)
    print(f"  PATCH {path} -> {response.status_code} {response.data}")


def _delete(path: str, data: object) -> None:
    request = factory.delete(path, json.dumps(data), content_type="application/json")
    response = ArticleViewSet.as_view({"delete": "bulk_destroy"})(request)
    print(f"  DELETE {path} -> {response.status_code} {response.data}")


def main() -> None:
    author = Author.objects.create(name="Ada Lovelace")

    print("== Bulk create (atomic, default): all valid ==")
    _post(
        "/articles/bulk/",
        [
            {"title": "First Post", "author": author.pk},
            {"title": "Second Post", "author": author.pk},
        ],
    )
    ids = list(Article.objects.values_list("id", flat=True))

    print("\n== Bulk create (atomic): one invalid item aborts the whole batch ==")
    _post(
        "/articles/bulk/",
        [{"title": "Would Succeed Alone", "author": author.pk}, {"title": "", "author": author.pk}],
    )
    print(f"  Article count unchanged: {Article.objects.count()}")

    print("\n== Bulk update ==")
    _put(
        "/articles/bulk-update/",
        [{"id": ids[0], "title": "First Post (Revised)", "author": author.pk}],
    )

    print("\n== Bulk partial update ==")
    _patch("/articles/bulk-partial-update/", [{"id": ids[0], "published": True}])

    print("\n== Bulk delete ==")
    _delete("/articles/bulk-delete/", ids)
    print(f"  Article count after delete: {Article.objects.count()}")

    print("\n== Non-atomic mode: partial success ==")
    with override_settings(BULK_OPERATIONS={"ATOMIC": False}):
        _post(
            "/articles/bulk/",
            [{"title": "Good Post", "author": author.pk}, {"title": "", "author": author.pk}],
        )


if __name__ == "__main__":
    runner = DiscoverRunner(run_syncdb=True)
    old_config = runner.setup_databases()
    try:
        main()
    finally:
        runner.teardown_databases(old_config)
