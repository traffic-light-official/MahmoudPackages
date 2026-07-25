"""Tests for :mod:`drf_api_reverse.codegen.serializers`."""

from __future__ import annotations

from typing import Any

from drf_api_reverse.codegen.serializers import (
    generate_serializer_regions,
    region_key,
    render_file,
)


class TestRegionKey:
    def test_format(self) -> None:
        assert region_key("Article") == "serializer:Article"


class TestGenerateSerializerRegions:
    def test_one_region_per_schema(self, sample_schema: dict[str, Any]) -> None:
        regions = generate_serializer_regions(sample_schema)
        assert set(regions) == {
            "serializer:Author",
            "serializer:Article",
            "serializer:Comment",
        }

    def test_dependency_is_emitted_before_dependent(self, sample_schema: dict[str, Any]) -> None:
        regions = generate_serializer_regions(sample_schema)
        keys = list(regions)
        assert keys.index("serializer:Author") < keys.index("serializer:Article")
        assert keys.index("serializer:Author") < keys.index("serializer:Comment")

    def test_nested_ref_becomes_nested_serializer_field(
        self, sample_schema: dict[str, Any]
    ) -> None:
        regions = generate_serializer_regions(sample_schema)
        assert "author = AuthorSerializer(required=False)" in regions["serializer:Article"]

    def test_array_of_primitives_field(self, sample_schema: dict[str, Any]) -> None:
        regions = generate_serializer_regions(sample_schema)
        assert "tags = serializers.ListField" in regions["serializer:Article"]

    def test_required_field_has_no_required_false(self, sample_schema: dict[str, Any]) -> None:
        regions = generate_serializer_regions(sample_schema)
        assert "title = serializers.CharField()" in regions["serializer:Article"]

    def test_empty_schema_generates_empty_class(self) -> None:
        schema = {"components": {"schemas": {"Empty": {"type": "object"}}}}
        regions = generate_serializer_regions(schema)
        assert (
            regions["serializer:Empty"]
            == "class EmptySerializer(serializers.Serializer):\n    pass"
        )

    def test_no_schemas_at_all_produces_no_regions(self) -> None:
        assert generate_serializer_regions({}) == {}


class TestCircularReferences:
    def test_second_class_in_a_cycle_degrades_to_dict_field(self) -> None:
        schema = {
            "components": {
                "schemas": {
                    "A": {
                        "type": "object",
                        "properties": {"b": {"$ref": "#/components/schemas/B"}},
                    },
                    "B": {
                        "type": "object",
                        "properties": {"a": {"$ref": "#/components/schemas/A"}},
                    },
                }
            }
        }
        regions = generate_serializer_regions(schema)
        bodies = list(regions.values())
        # Whichever class is emitted second must degrade its back-reference.
        assert any("circular/forward reference" in body for body in bodies)


class TestRenderFile:
    def test_includes_header_and_all_regions(self, sample_schema: dict[str, Any]) -> None:
        text = render_file(sample_schema)
        assert "from rest_framework import serializers" in text
        assert "class AuthorSerializer" in text
        assert "class ArticleSerializer" in text
        assert "class CommentSerializer" in text
        assert "BEGIN DRF-API-REVERSE GENERATED: serializer:Author" in text

    def test_is_valid_python(self, sample_schema: dict[str, Any]) -> None:
        text = render_file(sample_schema)
        compile(text, "<generated>", "exec")

    def test_empty_schema_still_has_a_header(self) -> None:
        text = render_file({})
        assert "from rest_framework import serializers" in text
