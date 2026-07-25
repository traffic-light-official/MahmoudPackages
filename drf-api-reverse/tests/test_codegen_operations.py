"""Tests for :mod:`drf_api_reverse.codegen.operations`."""

from __future__ import annotations

from typing import Any

from drf_api_reverse.codegen.operations import parse_resource_groups


class TestParseResourceGroups:
    def test_one_group_per_top_level_resource(self, sample_schema: dict[str, Any]) -> None:
        groups = parse_resource_groups(sample_schema)
        assert [g.key for g in groups] == ["articles"]

    def test_base_path_is_the_collection_path(self, sample_schema: dict[str, Any]) -> None:
        groups = parse_resource_groups(sample_schema)
        assert groups[0].base_path == "/articles/"

    def test_classifies_collection_operations(self, sample_schema: dict[str, Any]) -> None:
        (group,) = parse_resource_groups(sample_schema)
        collection_ops = {
            op.method: op.drf_method_name for op in group.operations if op.kind == "collection"
        }
        assert collection_ops == {"get": "list", "post": "create"}

    def test_classifies_detail_operations(self, sample_schema: dict[str, Any]) -> None:
        (group,) = parse_resource_groups(sample_schema)
        detail_ops = {
            op.method: op.drf_method_name for op in group.operations if op.kind == "detail"
        }
        assert detail_ops == {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}

    def test_classifies_nested_action(self, sample_schema: dict[str, Any]) -> None:
        (group,) = parse_resource_groups(sample_schema)
        nested = [op for op in group.operations if op.kind == "nested_action"]
        assert len(nested) == 1
        assert nested[0].action_url_path == "comments"
        assert nested[0].drf_method_name == "list_article_comments"

    def test_operation_id_used_for_nested_action_name(self) -> None:
        schema = {
            "paths": {
                "/things/": {"get": {"operationId": "listThings"}},
                "/things/{id}/": {"get": {"operationId": "getThing"}},
                "/things/{id}/history/": {"get": {"operationId": "getThingHistory"}},
            }
        }
        (group,) = parse_resource_groups(schema)
        nested = next(op for op in group.operations if op.kind == "nested_action")
        assert nested.drf_method_name == "get_thing_history"

    def test_missing_operation_id_falls_back_to_method_and_segment(self) -> None:
        schema = {
            "paths": {
                "/things/": {"get": {}},
                "/things/{id}/": {"get": {}},
                "/things/{id}/history/": {"get": {}},
            }
        }
        (group,) = parse_resource_groups(schema)
        nested = next(op for op in group.operations if op.kind == "nested_action")
        assert nested.drf_method_name == "get_history"

    def test_deeper_nesting_is_unsupported(self) -> None:
        schema = {
            "paths": {
                "/things/{id}/history/{event_id}/": {"get": {"operationId": "getEvent"}},
            }
        }
        (group,) = parse_resource_groups(schema)
        assert group.operations[0].kind == "unsupported"

    def test_unrecognized_method_on_collection_path_is_unsupported(self) -> None:
        schema = {"paths": {"/things/": {"head": {"operationId": "headThings"}}}}
        (group,) = parse_resource_groups(schema)
        assert group.operations[0].kind == "unsupported"

    def test_unrecognized_method_on_detail_path_is_unsupported(self) -> None:
        schema = {"paths": {"/things/{id}/": {"head": {"operationId": "headThing"}}}}
        (group,) = parse_resource_groups(schema)
        assert group.operations[0].kind == "unsupported"

    def test_two_path_params_is_unsupported(self) -> None:
        schema = {"paths": {"/things/{a}/{b}/": {"get": {"operationId": "x"}}}}
        (group,) = parse_resource_groups(schema)
        assert group.operations[0].kind == "unsupported"

    def test_empty_schema_produces_no_groups(self) -> None:
        assert parse_resource_groups({}) == []

    def test_operations_preserve_declaration_order(self, sample_schema: dict[str, Any]) -> None:
        (group,) = parse_resource_groups(sample_schema)
        paths_in_order = [op.path for op in group.operations]
        assert paths_in_order == [
            "/articles/",
            "/articles/",
            "/articles/{id}/",
            "/articles/{id}/",
            "/articles/{id}/",
            "/articles/{id}/comments/",
        ]
