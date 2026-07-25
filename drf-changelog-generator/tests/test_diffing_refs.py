"""Tests for :mod:`drf_changelog_generator.diffing.refs`."""

from __future__ import annotations

import pytest

from drf_changelog_generator.diffing.refs import deref, resolve_ref


class TestResolveRef:
    def test_resolves_a_nested_pointer(self) -> None:
        document = {"components": {"schemas": {"Article": {"type": "object"}}}}

        result = resolve_ref(document, "#/components/schemas/Article")

        assert result == {"type": "object"}

    def test_unescapes_json_pointer_special_characters(self) -> None:
        document = {"components": {"schemas": {"a/b": {"x~y": 1}}}}

        result = resolve_ref(document, "#/components/schemas/a~1b")

        assert result == {"x~y": 1}

    def test_rejects_non_local_references(self) -> None:
        with pytest.raises(ValueError, match="local"):
            resolve_ref({}, "https://example.com/schema.json")

    def test_raises_for_a_missing_key(self) -> None:
        with pytest.raises(ValueError, match="does not resolve"):
            resolve_ref({"components": {}}, "#/components/schemas/Missing")


class TestDeref:
    def test_returns_a_plain_schema_unchanged(self) -> None:
        schema = {"type": "string"}

        assert deref({}, schema) == schema

    def test_follows_a_single_ref(self) -> None:
        document = {"components": {"schemas": {"Article": {"type": "object"}}}}

        result = deref(document, {"$ref": "#/components/schemas/Article"})

        assert result == {"type": "object"}

    def test_follows_a_chain_of_refs(self) -> None:
        document = {
            "components": {
                "schemas": {
                    "A": {"$ref": "#/components/schemas/B"},
                    "B": {"type": "object"},
                }
            }
        }

        result = deref(document, {"$ref": "#/components/schemas/A"})

        assert result == {"type": "object"}

    def test_raises_on_circular_refs(self) -> None:
        document = {
            "components": {
                "schemas": {
                    "A": {"$ref": "#/components/schemas/B"},
                    "B": {"$ref": "#/components/schemas/A"},
                }
            }
        }

        with pytest.raises(ValueError, match="Circular"):
            deref(document, {"$ref": "#/components/schemas/A"})

    def test_non_dict_node_returns_empty_dict(self) -> None:
        assert deref({}, "not-a-schema") == {}
