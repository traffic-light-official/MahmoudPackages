"""Tests for :mod:`drf_api_reverse.codegen.urls`."""

from __future__ import annotations

from typing import Any

from drf_api_reverse.codegen.urls import generate_url_regions, region_key, render_file


class TestRegionKey:
    def test_format(self) -> None:
        assert region_key("articles") == "url:articles"


class TestGenerateUrlRegions:
    def test_one_region_per_resource_group(self, sample_schema: dict[str, Any]) -> None:
        regions = generate_url_regions(sample_schema)
        assert set(regions) == {"url:articles"}

    def test_registers_with_the_collection_prefix(self, sample_schema: dict[str, Any]) -> None:
        regions = generate_url_regions(sample_schema)
        assert regions["url:articles"] == (
            "router.register('articles', ArticlesViewSet, basename='articles')"
        )

    def test_prefix_with_a_quote_character_is_safely_escaped(self) -> None:
        schema = {"paths": {"/things'/": {"get": {"operationId": "listThings"}}}}
        body = generate_url_regions(schema)["url:things"]
        # Must be valid Python - a naive f-string quote would break here.
        compile(body, "<generated>", "exec")
        assert "things'" in body


class TestRenderFile:
    def test_is_valid_python(self, sample_schema: dict[str, Any]) -> None:
        text = render_file(sample_schema)
        compile(text, "<generated>", "exec")

    def test_includes_router_setup_and_urlpatterns(self, sample_schema: dict[str, Any]) -> None:
        text = render_file(sample_schema)
        assert "router = DefaultRouter()" in text
        assert "urlpatterns = router.urls" in text
        assert "from .views import *" in text

    def test_empty_schema_still_produces_a_valid_file(self) -> None:
        text = render_file({})
        compile(text, "<generated>", "exec")
        assert "urlpatterns = router.urls" in text
