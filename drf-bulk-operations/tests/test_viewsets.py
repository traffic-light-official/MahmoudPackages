"""Tests for :mod:`drf_bulk_operations.viewsets`.

The most important test in this file is the routing regression test:
DRF's router creates one URL ``Route`` per ``@action``-decorated
method, keyed only by its ``url_path`` - two independently decorated
actions sharing a ``url_path`` produce two colliding URL patterns for
the same path string, and only the first one registered is ever
actually reachable (confirmed empirically while building this
package - see ``docs/architecture.md``). If a future change ever gives
two of this package's bulk actions the same ``url_path`` again, this
test must catch it.
"""

from __future__ import annotations

from collections import Counter

from rest_framework.routers import DefaultRouter

from drf_bulk_operations import BulkModelViewSet
from tests.test_app.models import Article
from tests.test_app.serializers import ArticleSerializer


class _FullBulkViewSet(BulkModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer


class TestRoutingHasNoCollisions:
    def test_every_bulk_action_gets_its_own_reachable_url(self) -> None:
        router = DefaultRouter()
        router.register("articles", _FullBulkViewSet, basename="article")

        action_routes = [
            (str(url.pattern), tuple(sorted(url.callback.actions.items())))
            for url in router.urls
            if getattr(url.callback, "actions", None)
            and any(
                action in url.callback.actions.values()
                for action in (
                    "bulk_create",
                    "bulk_update",
                    "bulk_partial_update",
                    "bulk_destroy",
                )
            )
        ]

        # Every (pattern, method-mapping) pair must be unique - a repeated
        # pattern string bound to a *different* mapping is exactly the
        # collision bug: only the first-registered one would ever match.
        patterns = [pattern for pattern, _mapping in action_routes]
        duplicates = [pattern for pattern, count in Counter(patterns).items() if count > 1]
        assert not duplicates, f"Colliding URL pattern(s): {duplicates}"

        found_actions = {
            action for _pattern, mapping in action_routes for _method, action in mapping
        }
        assert found_actions == {
            "bulk_create",
            "bulk_update",
            "bulk_partial_update",
            "bulk_destroy",
        }


class TestBulkModelViewSetComposition:
    def test_has_all_four_bulk_actions(self) -> None:
        for action_name in ("bulk_create", "bulk_update", "bulk_partial_update", "bulk_destroy"):
            assert hasattr(_FullBulkViewSet, action_name)

    def test_is_still_a_regular_model_viewset(self) -> None:
        for action_name in ("list", "create", "retrieve", "update", "partial_update", "destroy"):
            assert hasattr(_FullBulkViewSet, action_name)
