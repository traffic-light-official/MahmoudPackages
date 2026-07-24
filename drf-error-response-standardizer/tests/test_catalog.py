"""Tests for :mod:`drf_error_response_standardizer.catalog`."""

from __future__ import annotations

import json

from django.test import override_settings

from drf_error_response_standardizer.catalog import build_catalog, render_json, render_markdown
from drf_error_response_standardizer.codes import ErrorType
from drf_error_response_standardizer.registry import ProblemRegistry


class TestBuildCatalog:
    def test_builds_one_entry_per_registered_error_type(self) -> None:
        registry = ProblemRegistry()
        registry.register(ValueError, ErrorType(code="a", title="A", slug="a", status=400))
        registry.register(TypeError, ErrorType(code="b", title="B", slug="b", status=409))

        catalog = build_catalog(registry)

        assert [entry["code"] for entry in catalog] == ["a", "b"]

    def test_entries_are_sorted_by_code(self) -> None:
        registry = ProblemRegistry()
        registry.register(ValueError, ErrorType(code="zeta", title="Z", slug="z", status=400))
        registry.register(TypeError, ErrorType(code="alpha", title="A", slug="a", status=400))

        catalog = build_catalog(registry)

        assert [entry["code"] for entry in catalog] == ["alpha", "zeta"]

    def test_type_uri_is_about_blank_without_base_uri(self) -> None:
        registry = ProblemRegistry()
        registry.register(ValueError, ErrorType(code="a", title="A", slug="a", status=400))

        catalog = build_catalog(registry)

        assert catalog[0]["type"] == "about:blank"

    def test_type_uri_uses_configured_base_uri(self) -> None:
        registry = ProblemRegistry()
        registry.register(ValueError, ErrorType(code="a", title="A", slug="a-slug", status=400))

        with override_settings(
            ERROR_RESPONSE_STANDARDIZER={"TYPE_BASE_URI": "https://api.example.com/problems/"}
        ):
            catalog = build_catalog(registry)

        assert catalog[0]["type"] == "https://api.example.com/problems/a-slug"

    def test_uses_default_registry_when_none_given(self) -> None:
        catalog = build_catalog()

        assert any(entry["code"] == "validation_error" for entry in catalog)


class TestRenderJson:
    def test_produces_valid_json_matching_the_catalog(self) -> None:
        catalog = [{"code": "a", "title": "A", "status": 400, "type": "about:blank"}]

        rendered = render_json(catalog)

        assert json.loads(rendered) == catalog

    def test_ends_with_a_trailing_newline(self) -> None:
        rendered = render_json([])

        assert rendered.endswith("\n")


class TestRenderMarkdown:
    def test_includes_a_heading_and_table_row_per_entry(self) -> None:
        catalog = [{"code": "a", "title": "A Problem", "status": 400, "type": "about:blank"}]

        rendered = render_markdown(catalog)

        assert "# Error Catalog" in rendered
        assert "`a`" in rendered
        assert "A Problem" in rendered
        assert "400" in rendered

    def test_empty_catalog_still_renders_heading_and_header_row(self) -> None:
        rendered = render_markdown([])

        assert "# Error Catalog" in rendered
        assert "| Code | Title | HTTP Status | Type URI |" in rendered
