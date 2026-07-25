"""Example: a ping view, an async permission, an async throttle, and full async CRUD.

Run with:

    python -m examples.blog.example
"""

from __future__ import annotations

import asyncio
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
        CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
        USE_TZ=True,
    )
    django.setup()

from django.test import AsyncRequestFactory
from django.test.runner import DiscoverRunner

from examples.blog.models import Article, Author
from examples.blog.views import (
    AllowRegisteredClients,
    ArticleViewSet,
    OncePerMinuteThrottle,
    PingView,
)

factory = AsyncRequestFactory()


async def demo_ping() -> None:
    print("== PingView ==")
    request = factory.get("/ping/")
    response = await PingView.as_view()(request)
    print(f"  GET /ping/ -> {response.status_code} {response.data}")


async def demo_async_permission() -> None:
    print("\n== Async-native permission ==")

    class Guarded(PingView):
        permission_classes = [AllowRegisteredClients]
        authentication_classes: list[type] = []  # see docs/troubleshooting.md

    request = factory.get("/guarded/")
    response = await Guarded.as_view()(request)
    print(f"  No X-Client-Id header -> {response.status_code} {response.data}")

    request = factory.get("/guarded/", headers={"X-Client-Id": "trusted-client"})
    response = await Guarded.as_view()(request)
    print(f"  Trusted X-Client-Id header -> {response.status_code} {response.data}")


async def demo_async_throttle() -> None:
    print("\n== Async-native throttle (1/min) ==")

    class Throttled(PingView):
        throttle_classes = [OncePerMinuteThrottle]

    request = factory.get("/throttled/", headers={"X-Client-Id": "client-a"})
    response = await Throttled.as_view()(request)
    print(f"  First request -> {response.status_code}")

    request = factory.get("/throttled/", headers={"X-Client-Id": "client-a"})
    response = await Throttled.as_view()(request)
    print(f"  Second request (same client) -> {response.status_code}")


async def demo_article_crud() -> None:
    print("\n== ArticleViewSet: full async CRUD ==")
    author = await Author.objects.acreate(name="Ada Lovelace")

    request = factory.post(
        "/articles/",
        data=json.dumps({"title": "Async Views in DRF", "author": author.pk}),
        content_type="application/json",
    )
    response = await ArticleViewSet.as_view({"post": "create"})(request)
    print(f"  POST /articles/ -> {response.status_code} {response.data}")
    article_id = response.data["id"]

    request = factory.get("/articles/")
    response = await ArticleViewSet.as_view({"get": "list"})(request)
    print(f"  GET /articles/ -> {response.status_code}, {len(response.data)} article(s)")

    request = factory.get(f"/articles/{article_id}/")
    response = await ArticleViewSet.as_view({"get": "retrieve"})(request, pk=article_id)
    print(f"  GET /articles/{article_id}/ -> {response.status_code} {response.data}")

    request = factory.patch(
        f"/articles/{article_id}/",
        data=json.dumps({"title": "Async Views in DRF (Updated)"}),
        content_type="application/json",
    )
    response = await ArticleViewSet.as_view({"patch": "partial_update"})(request, pk=article_id)
    print(f"  PATCH /articles/{article_id}/ -> {response.status_code} {response.data}")

    request = factory.delete(f"/articles/{article_id}/")
    response = await ArticleViewSet.as_view({"delete": "destroy"})(request, pk=article_id)
    print(f"  DELETE /articles/{article_id}/ -> {response.status_code}")

    remaining = [article.title async for article in Article.objects.all()]
    print(f"  Remaining articles: {remaining}")


async def main() -> None:
    await demo_ping()
    await demo_async_permission()
    await demo_async_throttle()
    await demo_article_crud()


if __name__ == "__main__":
    runner = DiscoverRunner(run_syncdb=True)
    old_config = runner.setup_databases()
    try:
        asyncio.run(main())
    finally:
        runner.teardown_databases(old_config)
