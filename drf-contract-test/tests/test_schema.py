"""Tests for drf_contract_test.schema."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from drf_contract_test.exceptions import SchemaLoadError
from drf_contract_test.schema import Schema, dump_schema_file, generate_schema, load_schema_file


class TestSchema:
    def test_version_and_title(self, minimal_openapi: dict[str, Any]) -> None:
        schema = Schema(minimal_openapi)
        assert schema.version == "1.0.0"
        assert schema.title == "Test API"

    def test_version_defaults_to_empty_string(self) -> None:
        assert Schema({}).version == ""
        assert Schema({}).title == ""

    def test_operations_yields_method_path_and_object(
        self, minimal_openapi: dict[str, Any]
    ) -> None:
        ops = list(Schema(minimal_openapi).operations())
        assert ("GET", "/articles/", minimal_openapi["paths"]["/articles/"]["get"]) in ops
        assert ("POST", "/articles/", minimal_openapi["paths"]["/articles/"]["post"]) in ops
        assert len(ops) == 2

    def test_operations_skips_non_method_keys(self) -> None:
        raw = {
            "paths": {
                "/x/": {"get": {"responses": {}}, "parameters": [], "summary": "not a method"}
            }
        }
        ops = list(Schema(raw).operations())
        assert len(ops) == 1
        assert ops[0][0] == "GET"

    def test_get_operation_found(self, minimal_openapi: dict[str, Any]) -> None:
        op = Schema(minimal_openapi).get_operation("get", "/articles/")
        assert op is not None
        assert op["operationId"] == "listArticles"

    def test_get_operation_missing_path(self, minimal_openapi: dict[str, Any]) -> None:
        assert Schema(minimal_openapi).get_operation("get", "/missing/") is None

    def test_get_operation_missing_method(self, minimal_openapi: dict[str, Any]) -> None:
        assert Schema(minimal_openapi).get_operation("delete", "/articles/") is None


class TestLoadSchemaFile:
    def test_loads_json(self, tmp_path: Path, minimal_openapi: dict[str, Any]) -> None:
        path = tmp_path / "schema.json"
        path.write_text(json.dumps(minimal_openapi), encoding="utf-8")
        schema = load_schema_file(path)
        assert schema.raw == minimal_openapi

    def test_loads_yaml(self, tmp_path: Path, minimal_openapi: dict[str, Any]) -> None:
        path = tmp_path / "schema.yaml"
        path.write_text(yaml.safe_dump(minimal_openapi), encoding="utf-8")
        schema = load_schema_file(path)
        assert schema.raw == minimal_openapi

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(SchemaLoadError, match="not found"):
            load_schema_file(tmp_path / "missing.yaml")

    def test_invalid_json_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "schema.json"
        path.write_text("{not valid json", encoding="utf-8")
        with pytest.raises(SchemaLoadError):
            load_schema_file(path)

    def test_non_object_content_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "schema.yaml"
        path.write_text("- just\n- a\n- list\n", encoding="utf-8")
        with pytest.raises(SchemaLoadError, match="did not contain"):
            load_schema_file(path)


class TestDumpSchemaFile:
    def test_round_trips_through_json(
        self, tmp_path: Path, minimal_openapi: dict[str, Any]
    ) -> None:
        path = tmp_path / "out.json"
        dump_schema_file(Schema(minimal_openapi), path)
        assert load_schema_file(path).raw == minimal_openapi

    def test_round_trips_through_yaml(
        self, tmp_path: Path, minimal_openapi: dict[str, Any]
    ) -> None:
        path = tmp_path / "out.yaml"
        dump_schema_file(Schema(minimal_openapi), path)
        assert load_schema_file(path).raw == minimal_openapi


@pytest.mark.django_db
class TestGenerateSchema:
    def test_generates_schema_from_live_project(self) -> None:
        schema = generate_schema()
        assert schema.title == "Test App API"
        assert schema.version == "1.0.0"
        paths = schema.raw.get("paths", {})
        assert "/articles/" in paths
        assert "/authors/" in paths

    def test_generated_schema_has_resolvable_component_refs(self) -> None:
        schema = generate_schema()
        op = schema.get_operation("get", "/articles/")
        assert op is not None
        assert "content" in op["responses"]["200"]
        assert "components" in schema.raw
        assert "schemas" in schema.raw["components"]
        assert "Article" in schema.raw["components"]["schemas"]
