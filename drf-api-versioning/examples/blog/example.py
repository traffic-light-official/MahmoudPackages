"""Example: a versioned endpoint with deprecation headers and registry enforcement.

Run with:

    python -m examples.blog.example
"""

from __future__ import annotations

import datetime
from typing import Any

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=False,
        ALLOWED_HOSTS=["*"],
        DATABASES={},
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "drf_api_versioning",
            "rest_framework",
        ],
        USE_TZ=True,
        API_VERSIONING={
            "VERSIONS": {
                "v1": {
                    "deprecated": datetime.date(2020, 1, 1),
                    "sunset": datetime.date(2020, 6, 1),
                    "deprecation_link": "https://example.com/docs/migrating-to-v3",
                },
                "v2": {
                    "deprecated": datetime.date(2020, 1, 1),
                    "deprecation_link": "https://example.com/docs/migrating-to-v3",
                },
                "v3": {},
            },
            "DEFAULT_VERSION": "v3",
        },
    )
    django.setup()

from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from drf_api_versioning import DeprecationHeaderMixin, URLPathVersioning, registry


class ArticleListView(DeprecationHeaderMixin, APIView):
    versioning_class = URLPathVersioning

    def get(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        return Response({"version": request.version, "articles": ["Hello, world!"]})


def _call(version: str) -> None:
    factory = APIRequestFactory()
    request = factory.get(f"/{version}/articles/")
    response = ArticleListView.as_view()(request, version=version)
    headers = {k: v for k, v in response.items() if k in ("Deprecation", "Sunset", "Link")}
    print(f"{version}: {response.status_code} {dict(response.data)} headers={headers}")


def main() -> None:
    """Call the endpoint at every declared version, plus one unknown version."""
    print("Registry:")
    for info in registry.all_versions():
        print(f"  {info}")

    print("\nRequests:")
    for version in ("v1", "v2", "v3", "v9"):
        _call(version)


if __name__ == "__main__":
    main()
