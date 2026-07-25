"""Tests for :mod:`drf_api_reverse.codegen.views`."""

from __future__ import annotations

from typing import Any

from drf_api_reverse.codegen.views import generate_viewset_regions, region_key, render_file


class TestRegionKey:
    def test_format(self) -> None:
        assert region_key("articles") == "viewset:articles"


class TestGenerateViewsetRegions:
    def test_one_region_per_resource_group(self, sample_schema: dict[str, Any]) -> None:
        regions = generate_viewset_regions(sample_schema)
        assert set(regions) == {"viewset:articles"}

    def test_class_name(self, sample_schema: dict[str, Any]) -> None:
        regions = generate_viewset_regions(sample_schema)
        assert "class ArticlesViewSet(viewsets.ViewSet):" in regions["viewset:articles"]

    def test_infers_serializer_class_from_response_ref(self, sample_schema: dict[str, Any]) -> None:
        regions = generate_viewset_regions(sample_schema)
        assert "serializer_class = ArticleSerializer" in regions["viewset:articles"]

    def test_generates_all_standard_methods(self, sample_schema: dict[str, Any]) -> None:
        body = generate_viewset_regions(sample_schema)["viewset:articles"]
        for method in ("list", "create", "retrieve", "partial_update", "destroy"):
            assert f"def {method}(self, request, *args, **kwargs):" in body

    def test_every_standard_method_raises_not_implemented(
        self, sample_schema: dict[str, Any]
    ) -> None:
        body = generate_viewset_regions(sample_schema)["viewset:articles"]
        assert body.count("raise NotImplementedError(") >= 6

    def test_nested_action_generates_action_decorator(self, sample_schema: dict[str, Any]) -> None:
        body = generate_viewset_regions(sample_schema)["viewset:articles"]
        assert "@action(detail=True, methods=['get'], url_path='comments')" in body
        assert "def list_article_comments(self, request, *args, **kwargs):" in body

    def test_no_serializer_ref_found_falls_back_to_none(self) -> None:
        schema = {"paths": {"/things/": {"get": {"operationId": "listThings"}}}}
        body = generate_viewset_regions(schema)["viewset:things"]
        assert "serializer_class = None" in body

    def test_infers_serializer_from_a_non_array_response_ref(self) -> None:
        schema = {
            "paths": {
                "/things/{id}/": {
                    "get": {
                        "operationId": "retrieveThing",
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/Thing"}
                                    }
                                }
                            }
                        },
                    }
                }
            }
        }
        body = generate_viewset_regions(schema)["viewset:things"]
        assert "serializer_class = ThingSerializer" in body

    def test_serializer_inference_skips_responses_without_a_ref(self) -> None:
        schema = {
            "paths": {
                "/things/{id}/": {
                    "get": {
                        "operationId": "retrieveThing",
                        "responses": {
                            "204": {},
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/Thing"}
                                    }
                                }
                            },
                        },
                    }
                }
            }
        }
        body = generate_viewset_regions(schema)["viewset:things"]
        assert "serializer_class = ThingSerializer" in body

    def test_unsupported_operation_gets_a_comment_not_code(self) -> None:
        schema = {"paths": {"/things/{a}/{b}/": {"get": {"operationId": "x"}}}}
        body = generate_viewset_regions(schema)["viewset:things"]
        assert "# Not auto-scaffolded: GET /things/{a}/{b}/ (unsupported shape)" in body
        assert "def " not in body

    def test_unsupported_path_comment_is_newline_safe(self) -> None:
        schema = {"paths": {"/things/\nimport os/{a}/{b}/": {"get": {"operationId": "x"}}}}
        body = generate_viewset_regions(schema)["viewset:things"]
        # The malicious newline must not have produced a second, uncommented line.
        code_lines = [line for line in body.splitlines() if not line.strip().startswith("#")]
        assert all("import os" not in line for line in code_lines)


class TestRenderFile:
    def test_is_valid_python(self, sample_schema: dict[str, Any]) -> None:
        text = render_file(sample_schema)
        compile(text, "<generated>", "exec")

    def test_includes_expected_imports(self, sample_schema: dict[str, Any]) -> None:
        text = render_file(sample_schema)
        assert "from rest_framework import viewsets" in text
        assert "from rest_framework.decorators import action" in text
        assert "from .serializers import *" in text
