"""Tests for drf_contract_test.diff."""

from __future__ import annotations

import copy
from typing import Any

from drf_contract_test.changes import Severity
from drf_contract_test.diff import compare_schemas
from drf_contract_test.schema import Schema


class TestEndpointDiffing:
    def test_removed_endpoint_is_breaking(self, minimal_openapi: dict[str, Any]) -> None:
        current = copy.deepcopy(minimal_openapi)
        del current["paths"]["/articles/"]["post"]
        result = compare_schemas(Schema(minimal_openapi), Schema(current))
        removed = [c for c in result.changes if c.kind == "endpoint_removed"]
        assert len(removed) == 1
        assert removed[0].severity is Severity.BREAKING
        assert removed[0].operation == "POST /articles/"

    def test_added_endpoint_is_safe(self, minimal_openapi: dict[str, Any]) -> None:
        baseline = copy.deepcopy(minimal_openapi)
        del baseline["paths"]["/articles/"]["post"]
        result = compare_schemas(Schema(baseline), Schema(minimal_openapi))
        added = [c for c in result.changes if c.kind == "endpoint_added"]
        assert len(added) == 1
        assert added[0].severity is Severity.SAFE

    def test_identical_schemas_produce_no_changes(self, minimal_openapi: dict[str, Any]) -> None:
        result = compare_schemas(Schema(minimal_openapi), Schema(copy.deepcopy(minimal_openapi)))
        assert result.changes == ()
        assert result.has_breaking_changes is False


class TestRequestDiffing:
    def test_new_required_request_field_is_breaking(self, minimal_openapi: dict[str, Any]) -> None:
        current = copy.deepcopy(minimal_openapi)
        current["components"]["schemas"]["ArticleRequest"]["properties"]["category"] = {
            "type": "string"
        }
        current["components"]["schemas"]["ArticleRequest"]["required"] = ["title", "category"]
        result = compare_schemas(Schema(minimal_openapi), Schema(current))
        assert result.has_breaking_changes
        assert any(c.kind == "field_added_required" for c in result.breaking_changes)

    def test_request_body_removed_is_breaking(self, minimal_openapi: dict[str, Any]) -> None:
        current = copy.deepcopy(minimal_openapi)
        del current["paths"]["/articles/"]["post"]["requestBody"]
        result = compare_schemas(Schema(minimal_openapi), Schema(current))
        assert any(
            c.kind == "request_body_removed" and c.severity is Severity.BREAKING
            for c in result.changes
        )

    def test_request_body_added_is_safe(self, minimal_openapi: dict[str, Any]) -> None:
        baseline = copy.deepcopy(minimal_openapi)
        del baseline["paths"]["/articles/"]["post"]["requestBody"]
        result = compare_schemas(Schema(baseline), Schema(minimal_openapi))
        assert any(
            c.kind == "request_body_added" and c.severity is Severity.SAFE for c in result.changes
        )


class TestResponseDiffing:
    def test_response_status_removed_is_breaking(self, minimal_openapi: dict[str, Any]) -> None:
        current = copy.deepcopy(minimal_openapi)
        current["paths"]["/articles/"]["post"]["responses"]["200"] = current["paths"]["/articles/"][
            "post"
        ]["responses"].pop("201")
        result = compare_schemas(Schema(minimal_openapi), Schema(current))
        assert any(
            c.kind == "response_removed"
            and c.location == "responses.201"
            and c.severity is Severity.BREAKING
            for c in result.changes
        )

    def test_response_status_added_is_safe(self, minimal_openapi: dict[str, Any]) -> None:
        current = copy.deepcopy(minimal_openapi)
        current["paths"]["/articles/"]["post"]["responses"]["400"] = {
            "content": {"application/json": {"schema": {"type": "object"}}}
        }
        result = compare_schemas(Schema(minimal_openapi), Schema(current))
        assert any(
            c.kind == "response_added" and c.severity is Severity.SAFE for c in result.changes
        )

    def test_response_field_removed_is_breaking(self, minimal_openapi: dict[str, Any]) -> None:
        current = copy.deepcopy(minimal_openapi)
        del current["components"]["schemas"]["Article"]["properties"]["status"]
        current["components"]["schemas"]["Article"]["required"] = ["id", "title"]
        result = compare_schemas(Schema(minimal_openapi), Schema(current))
        assert any(
            c.kind == "field_removed" and c.severity is Severity.BREAKING and "status" in c.location
            for c in result.changes
        )

    def test_response_enum_value_added_is_breaking(self, minimal_openapi: dict[str, Any]) -> None:
        current = copy.deepcopy(minimal_openapi)
        current["components"]["schemas"]["Article"]["properties"]["status"]["enum"].append(
            "archived"
        )
        result = compare_schemas(Schema(minimal_openapi), Schema(current))
        assert any(
            c.kind == "enum_value_added" and c.severity is Severity.BREAKING for c in result.changes
        )
