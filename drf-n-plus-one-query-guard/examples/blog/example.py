"""Example: catch and fix a real N+1 query, with no separate settings module.

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
            "examples.blog",
        ],
        USE_TZ=True,
    )
    django.setup()

from django.test.runner import DiscoverRunner

from drf_n_plus_one_query_guard import assert_no_n_plus_one
from examples.blog.models import Article, Author


def main() -> None:
    """Create test data, run an N+1-prone loop, catch it, then fix it."""
    runner = DiscoverRunner(run_syncdb=True)
    old_config = runner.setup_databases()

    for i in range(5):
        author = Author.objects.create(name=f"Author {i}")
        Article.objects.create(title=f"Article {i}", author=author)

    print("Unoptimized: expect an AssertionError...")
    try:
        with assert_no_n_plus_one():
            for article in Article.objects.all():
                print(f"  {article.title} by {article.author.name}")
    except AssertionError as exc:
        print(f"Caught: {exc}")

    print("\nOptimized with select_related('author'): expect no error...")
    with assert_no_n_plus_one():
        for article in Article.objects.select_related("author").all():
            print(f"  {article.title} by {article.author.name}")
    print("No N+1 detected.")

    runner.teardown_databases(old_config)


if __name__ == "__main__":
    main()
