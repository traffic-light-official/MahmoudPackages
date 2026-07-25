"""Tests for :mod:`drf_changelog_generator.diffing.engine`."""

from __future__ import annotations

from typing import Any

from drf_changelog_generator.changes import Change, ChangeKind, Severity
from drf_changelog_generator.diffing.engine import diff_schemas


def _find(changes: list[Change], **criteria: Any) -> Change | None:
    for change in changes:
        if all(getattr(change, key) == value for key, value in criteria.items()):
            return change
    return None


class TestEndpointChanges:
    def test_detects_added_endpoint(self, old_schema: dict, new_schema: dict) -> None:
        diff = diff_schemas(old_schema, new_schema)

        change = _find(
            diff.changes,
            kind=ChangeKind.ENDPOINT_ADDED,
            path="/articles/{id}/comments/",
            method="get",
        )
        assert change is not None
        assert change.severity is Severity.NON_BREAKING

    def test_detects_removed_endpoint(self, old_schema: dict, new_schema: dict) -> None:
        diff = diff_schemas(old_schema, new_schema)

        change = _find(
            diff.changes, kind=ChangeKind.ENDPOINT_REMOVED, path="/articles/{id}/", method="delete"
        )
        assert change is not None
        assert change.severity is Severity.BREAKING

    def test_detects_newly_deprecated_endpoint(self, old_schema: dict, new_schema: dict) -> None:
        diff = diff_schemas(old_schema, new_schema)

        change = _find(
            diff.changes, kind=ChangeKind.ENDPOINT_DEPRECATED, path="/articles/", method="post"
        )
        assert change is not None
        assert change.severity is Severity.NON_BREAKING

    def test_detects_newly_undeprecated_endpoint(self) -> None:
        old = {"paths": {"/x/": {"get": {"deprecated": True, "responses": {}}}}}
        new = {"paths": {"/x/": {"get": {"deprecated": False, "responses": {}}}}}

        diff = diff_schemas(old, new)

        change = _find(diff.changes, kind=ChangeKind.ENDPOINT_UNDEPRECATED)
        assert change is not None
        assert change.severity is Severity.NON_BREAKING

    def test_identical_schemas_produce_no_changes(self, old_schema: dict) -> None:
        diff = diff_schemas(old_schema, old_schema)

        assert diff.is_empty


class TestParameterChanges:
    def test_detects_removed_optional_parameter_as_breaking(
        self, old_schema: dict, new_schema: dict
    ) -> None:
        diff = diff_schemas(old_schema, new_schema)

        change = _find(
            diff.changes,
            kind=ChangeKind.PARAMETER_REMOVED,
            path="/articles/",
            method="get",
            location="parameters.search",
        )
        assert change is not None
        assert change.severity is Severity.BREAKING

    def test_added_required_parameter_is_breaking(self) -> None:
        old = {"paths": {"/x/": {"get": {"parameters": [], "responses": {}}}}}
        new = {
            "paths": {
                "/x/": {
                    "get": {
                        "parameters": [{"name": "id", "in": "query", "required": True}],
                        "responses": {},
                    }
                }
            }
        }

        diff = diff_schemas(old, new)

        change = _find(diff.changes, kind=ChangeKind.PARAMETER_ADDED)
        assert change is not None
        assert change.severity is Severity.BREAKING

    def test_added_optional_parameter_is_non_breaking(self) -> None:
        old = {"paths": {"/x/": {"get": {"parameters": [], "responses": {}}}}}
        new = {
            "paths": {
                "/x/": {
                    "get": {
                        "parameters": [{"name": "id", "in": "query", "required": False}],
                        "responses": {},
                    }
                }
            }
        }

        diff = diff_schemas(old, new)

        change = _find(diff.changes, kind=ChangeKind.PARAMETER_ADDED)
        assert change is not None
        assert change.severity is Severity.NON_BREAKING

    def test_parameter_becoming_required_is_breaking(self) -> None:
        old = {
            "paths": {
                "/x/": {
                    "get": {
                        "parameters": [{"name": "id", "in": "query", "required": False}],
                        "responses": {},
                    }
                }
            }
        }
        new = {
            "paths": {
                "/x/": {
                    "get": {
                        "parameters": [{"name": "id", "in": "query", "required": True}],
                        "responses": {},
                    }
                }
            }
        }

        diff = diff_schemas(old, new)

        change = _find(diff.changes, kind=ChangeKind.PARAMETER_REQUIRED_CHANGED)
        assert change is not None
        assert change.severity is Severity.BREAKING

    def test_parameter_becoming_optional_is_non_breaking(self) -> None:
        old = {
            "paths": {
                "/x/": {
                    "get": {
                        "parameters": [{"name": "id", "in": "query", "required": True}],
                        "responses": {},
                    }
                }
            }
        }
        new = {
            "paths": {
                "/x/": {
                    "get": {
                        "parameters": [{"name": "id", "in": "query", "required": False}],
                        "responses": {},
                    }
                }
            }
        }

        diff = diff_schemas(old, new)

        change = _find(diff.changes, kind=ChangeKind.PARAMETER_REQUIRED_CHANGED)
        assert change is not None
        assert change.severity is Severity.NON_BREAKING


class TestRequestFieldChanges:
    def test_removed_request_field_is_breaking(self, old_schema: dict, new_schema: dict) -> None:
        diff = diff_schemas(old_schema, new_schema)

        change = _find(
            diff.changes,
            kind=ChangeKind.REQUEST_FIELD_REMOVED,
            path="/articles/",
            method="post",
            location="body.legacy_id",
        )
        assert change is not None
        assert change.severity is Severity.BREAKING

    def test_added_required_request_field_is_breaking(
        self, old_schema: dict, new_schema: dict
    ) -> None:
        diff = diff_schemas(old_schema, new_schema)

        change = _find(
            diff.changes,
            kind=ChangeKind.REQUEST_FIELD_ADDED,
            path="/articles/",
            method="post",
            location="body.tags",
        )
        assert change is not None
        assert change.severity is Severity.BREAKING

    def test_added_optional_request_field_is_non_breaking(self) -> None:
        old = _request_schema_op({"title": {"type": "string"}}, required=["title"])
        new = _request_schema_op(
            {"title": {"type": "string"}, "note": {"type": "string"}}, required=["title"]
        )

        diff = diff_schemas(old, new)

        change = _find(diff.changes, kind=ChangeKind.REQUEST_FIELD_ADDED)
        assert change is not None
        assert change.severity is Severity.NON_BREAKING

    def test_request_field_type_change_is_breaking(self) -> None:
        old = _request_schema_op({"count": {"type": "integer"}})
        new = _request_schema_op({"count": {"type": "string"}})

        diff = diff_schemas(old, new)

        change = _find(diff.changes, kind=ChangeKind.REQUEST_FIELD_TYPE_CHANGED)
        assert change is not None
        assert change.severity is Severity.BREAKING
        assert "integer -> string" in change.message

    def test_request_field_becoming_required_is_breaking(self) -> None:
        old = _request_schema_op({"note": {"type": "string"}}, required=[])
        new = _request_schema_op({"note": {"type": "string"}}, required=["note"])

        diff = diff_schemas(old, new)

        change = _find(diff.changes, kind=ChangeKind.REQUEST_FIELD_REQUIRED_CHANGED)
        assert change is not None
        assert change.severity is Severity.BREAKING

    def test_request_field_becoming_optional_is_non_breaking(self) -> None:
        old = _request_schema_op({"note": {"type": "string"}}, required=["note"])
        new = _request_schema_op({"note": {"type": "string"}}, required=[])

        diff = diff_schemas(old, new)

        change = _find(diff.changes, kind=ChangeKind.REQUEST_FIELD_REQUIRED_CHANGED)
        assert change is not None
        assert change.severity is Severity.NON_BREAKING


class TestResponseFieldChanges:
    def test_removed_response_field_is_breaking(self, old_schema: dict, new_schema: dict) -> None:
        diff = diff_schemas(old_schema, new_schema)

        change = _find(
            diff.changes,
            kind=ChangeKind.RESPONSE_FIELD_REMOVED,
            path="/articles/",
            method="get",
            location="responses.200.legacy_id",
        )
        assert change is not None
        assert change.severity is Severity.BREAKING

    def test_added_response_field_is_always_non_breaking(
        self, old_schema: dict, new_schema: dict
    ) -> None:
        diff = diff_schemas(old_schema, new_schema)

        change = _find(
            diff.changes,
            kind=ChangeKind.RESPONSE_FIELD_ADDED,
            path="/articles/",
            method="get",
            location="responses.200.tags",
        )
        assert change is not None
        assert change.severity is Severity.NON_BREAKING

    def test_added_response_status_code_is_non_breaking(self) -> None:
        old = {"paths": {"/x/": {"get": {"responses": {"200": {}}}}}}
        new = {"paths": {"/x/": {"get": {"responses": {"200": {}, "404": {}}}}}}

        diff = diff_schemas(old, new)

        change = _find(diff.changes, kind=ChangeKind.RESPONSE_ADDED)
        assert change is not None
        assert change.severity is Severity.NON_BREAKING

    def test_removed_response_status_code_is_breaking(self) -> None:
        old = {"paths": {"/x/": {"get": {"responses": {"200": {}, "404": {}}}}}}
        new = {"paths": {"/x/": {"get": {"responses": {"200": {}}}}}}

        diff = diff_schemas(old, new)

        change = _find(diff.changes, kind=ChangeKind.RESPONSE_REMOVED)
        assert change is not None
        assert change.severity is Severity.BREAKING


class TestNestedSchemas:
    def test_diffs_nested_object_fields(self) -> None:
        old = _request_schema_op(
            {"author": {"type": "object", "properties": {"name": {"type": "string"}}}}
        )
        new = _request_schema_op(
            {
                "author": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}, "email": {"type": "string"}},
                }
            }
        )

        diff = diff_schemas(old, new)

        change = _find(
            diff.changes, kind=ChangeKind.REQUEST_FIELD_ADDED, location="body.author.email"
        )
        assert change is not None

    def test_diffs_array_item_fields(self) -> None:
        old = _request_schema_op(
            {
                "tags": {
                    "type": "array",
                    "items": {"type": "object", "properties": {"label": {"type": "string"}}},
                }
            }
        )
        new = _request_schema_op(
            {
                "tags": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"label": {"type": "string"}, "color": {"type": "string"}},
                    },
                }
            }
        )

        diff = diff_schemas(old, new)

        change = _find(
            diff.changes, kind=ChangeKind.REQUEST_FIELD_ADDED, location="body.tags[].color"
        )
        assert change is not None

    def test_resolves_refs_before_diffing(self) -> None:
        old = {
            "components": {
                "schemas": {"Widget": {"type": "object", "properties": {"a": {"type": "string"}}}}
            },
            "paths": {
                "/x/": {
                    "post": {
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Widget"}
                                }
                            }
                        },
                        "responses": {},
                    }
                }
            },
        }
        new = {
            "components": {
                "schemas": {
                    "Widget": {
                        "type": "object",
                        "properties": {"a": {"type": "string"}, "b": {"type": "string"}},
                    }
                }
            },
            "paths": {
                "/x/": {
                    "post": {
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Widget"}
                                }
                            }
                        },
                        "responses": {},
                    }
                }
            },
        }

        diff = diff_schemas(old, new)

        change = _find(diff.changes, kind=ChangeKind.REQUEST_FIELD_ADDED, location="body.b")
        assert change is not None


def _request_schema_op(
    properties: dict[str, Any], *, required: list[str] | None = None
) -> dict[str, Any]:
    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required is not None:
        schema["required"] = required
    return {
        "paths": {
            "/x/": {
                "post": {
                    "requestBody": {"content": {"application/json": {"schema": schema}}},
                    "responses": {},
                }
            }
        }
    }
