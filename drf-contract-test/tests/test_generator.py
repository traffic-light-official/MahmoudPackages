"""Tests for drf_contract_test.generator."""

from __future__ import annotations

from typing import Any

from drf_contract_test.generator import (
    ContractCase,
    _inline_refs,
    generate_contract_cases,
    validate_response_against_schema,
)
from drf_contract_test.schema import Schema


class TestGenerateContractCases:
    def test_one_case_per_status_per_operation(self, minimal_openapi: dict[str, Any]) -> None:
        cases = generate_contract_cases(Schema(minimal_openapi))
        assert len(cases) == 2
        by_op = {c.operation: c for c in cases}
        assert "GET /articles/" in by_op
        assert "POST /articles/" in by_op
        assert by_op["GET /articles/"].expected_status == "200"
        assert by_op["POST /articles/"].expected_status == "201"

    def test_filters_by_status(self, minimal_openapi: dict[str, Any]) -> None:
        cases = generate_contract_cases(Schema(minimal_openapi), statuses={"201"})
        assert len(cases) == 1
        assert cases[0].expected_status == "201"

    def test_skips_non_numeric_status_codes(self) -> None:
        raw: dict[str, Any] = {
            "paths": {
                "/x/": {
                    "get": {
                        "responses": {
                            "200": {
                                "content": {"application/json": {"schema": {"type": "object"}}}
                            },
                            "default": {
                                "content": {"application/json": {"schema": {"type": "object"}}}
                            },
                        }
                    }
                }
            }
        }
        cases = generate_contract_cases(Schema(raw))
        assert len(cases) == 1
        assert cases[0].expected_status == "200"

    def test_response_schema_none_when_no_json_content(self) -> None:
        raw: dict[str, Any] = {"paths": {"/x/": {"delete": {"responses": {"204": {}}}}}}
        cases = generate_contract_cases(Schema(raw))
        assert len(cases) == 1
        assert cases[0].response_schema is None


class TestValidateResponseAgainstSchema:
    def _case(self, schema: dict[str, Any] | None, status: str = "200") -> ContractCase:
        return ContractCase(
            operation="GET /x/",
            method="GET",
            path="/x/",
            expected_status=status,
            response_schema=schema,
        )

    def test_status_mismatch_reported(self) -> None:
        violations = validate_response_against_schema(
            self._case({"type": "object"}), status_code=404, data={}, root={}
        )
        assert len(violations) == 1
        assert "expected status 200" in violations[0]

    def test_no_schema_documented_means_no_violations(self) -> None:
        violations = validate_response_against_schema(
            self._case(None), status_code=200, data={"anything": 1}, root={}
        )
        assert violations == []

    def test_valid_response_has_no_violations(self) -> None:
        schema = {"type": "object", "properties": {"id": {"type": "integer"}}, "required": ["id"]}
        violations = validate_response_against_schema(
            self._case(schema), status_code=200, data={"id": 1}, root={}
        )
        assert violations == []

    def test_invalid_response_reports_violation(self) -> None:
        schema = {"type": "object", "properties": {"id": {"type": "integer"}}, "required": ["id"]}
        violations = validate_response_against_schema(
            self._case(schema), status_code=200, data={}, root={}
        )
        assert len(violations) == 1
        assert "id" in violations[0]

    def test_ref_schema_is_resolved_before_validating(self) -> None:
        root = {
            "components": {
                "schemas": {
                    "Widget": {
                        "type": "object",
                        "properties": {"n": {"type": "integer"}},
                        "required": ["n"],
                    }
                }
            }
        }
        case = self._case({"$ref": "#/components/schemas/Widget"})
        violations = validate_response_against_schema(
            case, status_code=200, data={"n": "not an int"}, root=root
        )
        assert len(violations) == 1

    def test_ref_schema_valid_data_passes(self) -> None:
        root = {
            "components": {
                "schemas": {
                    "Widget": {
                        "type": "object",
                        "properties": {"n": {"type": "integer"}},
                        "required": ["n"],
                    }
                }
            }
        }
        case = self._case({"$ref": "#/components/schemas/Widget"})
        violations = validate_response_against_schema(
            case, status_code=200, data={"n": 5}, root=root
        )
        assert violations == []


class TestInlineRefs:
    def test_simple_ref_inlined(self) -> None:
        root = {"components": {"schemas": {"Widget": {"type": "string"}}}}
        result = _inline_refs({"$ref": "#/components/schemas/Widget"}, root)
        assert result == {"type": "string"}

    def test_nested_property_ref_inlined(self) -> None:
        root = {
            "components": {
                "schemas": {
                    "Author": {"type": "object", "properties": {"name": {"type": "string"}}},
                }
            }
        }
        schema = {
            "type": "object",
            "properties": {"author": {"$ref": "#/components/schemas/Author"}},
        }
        result = _inline_refs(schema, root)
        assert result["properties"]["author"] == {
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }

    def test_items_ref_inlined(self) -> None:
        root = {"components": {"schemas": {"Tag": {"type": "string"}}}}
        schema = {"type": "array", "items": {"$ref": "#/components/schemas/Tag"}}
        result = _inline_refs(schema, root)
        assert result == {"type": "array", "items": {"type": "string"}}

    def test_broken_ref_left_unresolved(self) -> None:
        result = _inline_refs({"$ref": "#/components/schemas/Missing"}, {})
        assert result == {"$ref": "#/components/schemas/Missing"}

    def test_cycle_does_not_infinite_loop(self) -> None:
        root = {
            "components": {
                "schemas": {
                    "Node": {
                        "type": "object",
                        "properties": {
                            "children": {
                                "type": "array",
                                "items": {"$ref": "#/components/schemas/Node"},
                            }
                        },
                    }
                }
            }
        }
        result = _inline_refs({"$ref": "#/components/schemas/Node"}, root)
        # Should terminate; the cyclic branch bottoms out at a generic object.
        assert result["type"] == "object"
        children_items = result["properties"]["children"]["items"]
        assert children_items == {"type": "object"}
