"""Tests for the directional schema-comparison rules in drf_contract_test.rules.

This is the most important module in the package: the same structural
difference must be classified oppositely depending on whether it's a
request or a response schema. Every scenario below is tested in both
directions to pin down that behavior precisely.
"""

from __future__ import annotations

from typing import Any

from drf_contract_test.changes import Change, Severity
from drf_contract_test.rules import Direction, _resolve, compare_schema_objects


def _compare(
    old: dict[str, Any],
    new: dict[str, Any],
    direction: Direction,
    root: dict[str, Any] | None = None,
) -> list[Change]:
    root = root or {}
    return compare_schema_objects(
        old,
        new,
        direction=direction,
        location="x",
        operation="GET /x/",
        old_root=root,
        new_root=root,
    )


class TestTypeChanges:
    def test_type_change_is_always_breaking_in_request(self) -> None:
        changes = _compare({"type": "string"}, {"type": "integer"}, Direction.REQUEST)
        assert len(changes) == 1
        assert changes[0].severity is Severity.BREAKING
        assert changes[0].kind == "type_changed"

    def test_type_change_is_always_breaking_in_response(self) -> None:
        changes = _compare({"type": "string"}, {"type": "integer"}, Direction.RESPONSE)
        assert len(changes) == 1
        assert changes[0].severity is Severity.BREAKING

    def test_no_change_when_types_match(self) -> None:
        assert _compare({"type": "string"}, {"type": "string"}, Direction.REQUEST) == []

    def test_no_change_when_either_type_missing(self) -> None:
        assert _compare({}, {"type": "string"}, Direction.REQUEST) == []
        assert _compare({"type": "string"}, {}, Direction.REQUEST) == []


class TestNullable:
    def test_request_gaining_nullable_is_safe(self) -> None:
        changes = _compare(
            {"type": "string"}, {"type": "string", "nullable": True}, Direction.REQUEST
        )
        assert len(changes) == 1
        assert changes[0].severity is Severity.SAFE
        assert changes[0].kind == "nullable_added"

    def test_request_losing_nullable_is_breaking(self) -> None:
        changes = _compare(
            {"type": "string", "nullable": True}, {"type": "string"}, Direction.REQUEST
        )
        assert len(changes) == 1
        assert changes[0].severity is Severity.BREAKING
        assert changes[0].kind == "nullable_removed"

    def test_response_gaining_nullable_is_breaking(self) -> None:
        changes = _compare(
            {"type": "string"}, {"type": "string", "nullable": True}, Direction.RESPONSE
        )
        assert len(changes) == 1
        assert changes[0].severity is Severity.BREAKING

    def test_response_losing_nullable_is_safe(self) -> None:
        changes = _compare(
            {"type": "string", "nullable": True}, {"type": "string"}, Direction.RESPONSE
        )
        assert len(changes) == 1
        assert changes[0].severity is Severity.SAFE

    def test_openapi_31_style_null_type_union_is_recognized(self) -> None:
        changes = _compare({"type": "string"}, {"type": ["string", "null"]}, Direction.RESPONSE)
        assert len(changes) == 1
        assert changes[0].kind == "nullable_added"

    def test_no_change_when_nullable_unchanged(self) -> None:
        assert (
            _compare(
                {"type": "string", "nullable": True},
                {"type": "string", "nullable": True},
                Direction.REQUEST,
            )
            == []
        )


class TestEnum:
    def test_request_removing_enum_value_is_breaking(self) -> None:
        changes = _compare(
            {"type": "string", "enum": ["a", "b"]},
            {"type": "string", "enum": ["a"]},
            Direction.REQUEST,
        )
        assert len(changes) == 1
        assert changes[0].severity is Severity.BREAKING
        assert changes[0].kind == "enum_value_removed"

    def test_request_adding_enum_value_is_safe(self) -> None:
        changes = _compare(
            {"type": "string", "enum": ["a"]},
            {"type": "string", "enum": ["a", "b"]},
            Direction.REQUEST,
        )
        assert len(changes) == 1
        assert changes[0].severity is Severity.SAFE
        assert changes[0].kind == "enum_value_added"

    def test_response_adding_enum_value_is_breaking(self) -> None:
        changes = _compare(
            {"type": "string", "enum": ["a"]},
            {"type": "string", "enum": ["a", "b"]},
            Direction.RESPONSE,
        )
        assert len(changes) == 1
        assert changes[0].severity is Severity.BREAKING
        assert changes[0].kind == "enum_value_added"

    def test_response_removing_enum_value_is_safe(self) -> None:
        changes = _compare(
            {"type": "string", "enum": ["a", "b"]},
            {"type": "string", "enum": ["a"]},
            Direction.RESPONSE,
        )
        assert len(changes) == 1
        assert changes[0].severity is Severity.SAFE
        assert changes[0].kind == "enum_value_removed"

    def test_no_enum_change_reported_when_unchanged(self) -> None:
        assert _compare({"enum": ["a", "b"]}, {"enum": ["b", "a"]}, Direction.REQUEST) == []

    def test_both_added_and_removed_reported_together(self) -> None:
        changes = _compare({"enum": ["a", "b"]}, {"enum": ["b", "c"]}, Direction.REQUEST)
        kinds = {c.kind for c in changes}
        assert kinds == {"enum_value_removed", "enum_value_added"}


class TestProperties:
    def test_request_new_optional_field_is_safe(self) -> None:
        changes = _compare(
            {"type": "object", "properties": {"a": {"type": "string"}}, "required": []},
            {
                "type": "object",
                "properties": {"a": {"type": "string"}, "b": {"type": "string"}},
                "required": [],
            },
            Direction.REQUEST,
        )
        assert len(changes) == 1
        assert changes[0].severity is Severity.SAFE
        assert changes[0].kind == "field_added_optional"

    def test_request_new_required_field_is_breaking(self) -> None:
        changes = _compare(
            {"type": "object", "properties": {"a": {"type": "string"}}, "required": ["a"]},
            {
                "type": "object",
                "properties": {"a": {"type": "string"}, "b": {"type": "string"}},
                "required": ["a", "b"],
            },
            Direction.REQUEST,
        )
        assert len(changes) == 1
        assert changes[0].severity is Severity.BREAKING
        assert changes[0].kind == "field_added_required"

    def test_request_field_removed_is_safe(self) -> None:
        changes = _compare(
            {"type": "object", "properties": {"a": {"type": "string"}, "b": {"type": "string"}}},
            {"type": "object", "properties": {"a": {"type": "string"}}},
            Direction.REQUEST,
        )
        assert len(changes) == 1
        assert changes[0].severity is Severity.SAFE
        assert changes[0].kind == "field_removed"

    def test_response_new_field_is_always_safe(self) -> None:
        changes = _compare(
            {"type": "object", "properties": {"a": {"type": "string"}}},
            {"type": "object", "properties": {"a": {"type": "string"}, "b": {"type": "string"}}},
            Direction.RESPONSE,
        )
        assert len(changes) == 1
        assert changes[0].severity is Severity.SAFE
        assert changes[0].kind == "field_added"

    def test_response_field_removed_is_breaking(self) -> None:
        changes = _compare(
            {"type": "object", "properties": {"a": {"type": "string"}, "b": {"type": "string"}}},
            {"type": "object", "properties": {"a": {"type": "string"}}},
            Direction.RESPONSE,
        )
        assert len(changes) == 1
        assert changes[0].severity is Severity.BREAKING
        assert changes[0].kind == "field_removed"

    def test_no_properties_no_changes(self) -> None:
        assert _compare({"type": "object"}, {"type": "object"}, Direction.REQUEST) == []

    def test_nested_property_changes_are_recursively_detected(self) -> None:
        changes = _compare(
            {"type": "object", "properties": {"a": {"type": "string"}}},
            {"type": "object", "properties": {"a": {"type": "integer"}}},
            Direction.REQUEST,
        )
        assert len(changes) == 1
        assert changes[0].kind == "type_changed"
        assert changes[0].location == "x.properties.a"


class TestRequired:
    def test_request_optional_to_required_is_breaking(self) -> None:
        changes = _compare(
            {"type": "object", "properties": {"a": {"type": "string"}}, "required": []},
            {"type": "object", "properties": {"a": {"type": "string"}}, "required": ["a"]},
            Direction.REQUEST,
        )
        assert any(c.kind == "required_added" and c.severity is Severity.BREAKING for c in changes)

    def test_request_required_to_optional_is_safe(self) -> None:
        changes = _compare(
            {"type": "object", "properties": {"a": {"type": "string"}}, "required": ["a"]},
            {"type": "object", "properties": {"a": {"type": "string"}}, "required": []},
            Direction.REQUEST,
        )
        assert any(c.kind == "required_removed" and c.severity is Severity.SAFE for c in changes)

    def test_response_optional_to_required_is_safe(self) -> None:
        changes = _compare(
            {"type": "object", "properties": {"a": {"type": "string"}}, "required": []},
            {"type": "object", "properties": {"a": {"type": "string"}}, "required": ["a"]},
            Direction.RESPONSE,
        )
        assert any(c.kind == "required_added" and c.severity is Severity.SAFE for c in changes)

    def test_response_required_to_optional_is_breaking(self) -> None:
        changes = _compare(
            {"type": "object", "properties": {"a": {"type": "string"}}, "required": ["a"]},
            {"type": "object", "properties": {"a": {"type": "string"}}, "required": []},
            Direction.RESPONSE,
        )
        assert any(
            c.kind == "required_removed" and c.severity is Severity.BREAKING for c in changes
        )


class TestItems:
    def test_array_item_type_change_detected(self) -> None:
        changes = _compare(
            {"type": "array", "items": {"type": "string"}},
            {"type": "array", "items": {"type": "integer"}},
            Direction.RESPONSE,
        )
        assert len(changes) == 1
        assert changes[0].kind == "type_changed"
        assert changes[0].location == "x.items"

    def test_no_items_no_change(self) -> None:
        assert _compare({"type": "array"}, {"type": "array"}, Direction.RESPONSE) == []


class TestRefResolution:
    def test_ref_is_resolved_against_root(self) -> None:
        root = {"components": {"schemas": {"Widget": {"type": "string"}}}}
        changes = _compare(
            {"$ref": "#/components/schemas/Widget"}, {"type": "integer"}, Direction.REQUEST, root
        )
        assert len(changes) == 1
        assert changes[0].kind == "type_changed"

    def test_both_sides_can_be_refs(self) -> None:
        root = {
            "components": {
                "schemas": {
                    "A": {"type": "object", "properties": {"x": {"type": "string"}}},
                    "B": {"type": "object", "properties": {"x": {"type": "integer"}}},
                }
            }
        }
        changes = _compare(
            {"$ref": "#/components/schemas/A"},
            {"$ref": "#/components/schemas/B"},
            Direction.RESPONSE,
            root,
        )
        assert len(changes) == 1
        assert changes[0].location == "x.properties.x"

    def test_broken_ref_treated_as_opaque_not_a_crash(self) -> None:
        resolved = _resolve({"$ref": "#/components/schemas/Missing"}, {})
        assert resolved == {"$ref": "#/components/schemas/Missing"}

    def test_external_ref_not_followed(self) -> None:
        resolved = _resolve({"$ref": "other.yaml#/Widget"}, {})
        assert resolved == {"$ref": "other.yaml#/Widget"}

    def test_ref_cycle_does_not_infinite_loop(self) -> None:
        root = {
            "components": {
                "schemas": {
                    "Comment": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "replies": {
                                "type": "array",
                                "items": {"$ref": "#/components/schemas/Comment"},
                            },
                        },
                    }
                }
            }
        }
        # Should terminate without a RecursionError, even though Comment
        # transitively references itself through "replies".
        changes = _compare(
            {"$ref": "#/components/schemas/Comment"},
            {"$ref": "#/components/schemas/Comment"},
            Direction.RESPONSE,
            root,
        )
        assert changes == []
