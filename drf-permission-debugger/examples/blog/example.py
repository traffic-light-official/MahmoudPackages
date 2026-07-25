"""Example: seeing exactly why a permission check granted or denied a request.

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
            "drf_permission_debugger",
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

from drf_permission_debugger import describe_view
from examples.blog.models import Article
from examples.blog.views import ArticleViewSet


def main() -> None:
    owner = User.objects.create_user(
        username="ada",
        password="password",
        is_staff=True,
    )
    other_staff_user = User.objects.create_user(
        username="grace",
        password="password",
        is_staff=True,
    )
    article = Article.objects.create(title="Article on Permissions", owner=owner)

    client = APIClient()

    print("== Owner retrieves their own article: granted, no trace (debugger disabled) ==")
    client.force_authenticate(user=owner)
    response = client.get(f"/articles/{article.pk}/")
    print(f"  GET /articles/{article.pk}/ -> {response.status_code}")
    print(f"  X-Permission-Trace present: {'X-Permission-Trace' in response.headers}")

    print("\n== Same request, debugger enabled: granted, trace still attached ==")
    with override_settings(PERMISSION_DEBUGGER={"ENABLED": True}):
        response = client.get(f"/articles/{article.pk}/")
    print(f"  GET /articles/{article.pk}/ -> {response.status_code}")
    print(f"  X-Permission-Trace: {response.headers['X-Permission-Trace']}")

    print("\n== A different staff user retrieves it: denied, full trace ==")
    client.force_authenticate(user=other_staff_user)
    with override_settings(PERMISSION_DEBUGGER={"ENABLED": True, "INCLUDE_IN_RESPONSE_BODY": True}):
        response = client.get(f"/articles/{article.pk}/")
    print(f"  GET /articles/{article.pk}/ -> {response.status_code}")
    print(f"  X-Permission-Trace: {response.headers['X-Permission-Trace']}")
    print(f"  Body: {response.json()}")

    print("\n== Static introspection, no request at all ==")
    description = describe_view(ArticleViewSet)
    for permission in description["permissions"]:
        marker = " (object-level)" if permission.checks_object_permission else ""
        print(f"  {permission.name}{marker}: {permission.docstring}")


if __name__ == "__main__":
    runner = DiscoverRunner(run_syncdb=True)
    old_config = runner.setup_databases()
    try:
        main()
    finally:
        runner.teardown_databases(old_config)
