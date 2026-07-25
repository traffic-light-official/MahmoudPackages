"""Example: finding (and fixing) a slow, N+1-prone serializer field.

Run with:

    python -m examples.blog.example
"""

from __future__ import annotations

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
            "drf_serializer_performance_profiler",
            "examples.blog",
        ],
        ROOT_URLCONF="examples.blog.urls",
        USE_TZ=True,
    )
    django.setup()

from django.contrib.auth.models import User
from django.test import override_settings
from django.test.runner import DiscoverRunner
from rest_framework.test import APIClient

from examples.blog.models import Article, Author, Comment


def main() -> None:
    staff = User.objects.create_user(username="ada", is_staff=True)
    author = Author.objects.create(name="Ada Lovelace")
    for i in range(3):
        article = Article.objects.create(title=f"Article {i}", author=author)
        for j in range(2):
            Comment.objects.create(article=article, body=f"Comment {j}")

    client = APIClient()
    client.force_authenticate(user=staff)

    print("== Unoptimized: comment_count runs one query per row ==")
    with override_settings(SERIALIZER_PROFILER={"ENABLED": True}):
        response = client.get("/articles/")
    print(f"  Status: {response.status_code}, articles: {len(response.json())}")
    print(f"  X-Serializer-Profile: {response.headers['X-Serializer-Profile']}")

    print("\n== Optimized: comment_count is a queryset annotation ==")
    with override_settings(SERIALIZER_PROFILER={"ENABLED": True}):
        response = client.get("/optimized-articles/")
    print(f"  Status: {response.status_code}, articles: {len(response.json())}")
    print(f"  X-Serializer-Profile: {response.headers['X-Serializer-Profile']}")


if __name__ == "__main__":
    runner = DiscoverRunner(run_syncdb=True)
    old_config = runner.setup_databases()
    try:
        main()
    finally:
        runner.teardown_databases(old_config)
