"""Unit tests for schema-hash versioning."""

from __future__ import annotations

from drf_llm_gateway.versioning import compute_schema_hash


class TestComputeSchemaHash:
    def test_deterministic_for_identical_schema(self) -> None:
        schema = {"type": "object", "properties": {"a": {"type": "string"}}}
        assert compute_schema_hash(schema) == compute_schema_hash(schema)

    def test_key_order_does_not_affect_hash(self) -> None:
        a = {"type": "object", "properties": {"a": {"type": "string"}, "b": {"type": "integer"}}}
        b = {"properties": {"b": {"type": "integer"}, "a": {"type": "string"}}, "type": "object"}
        assert compute_schema_hash(a) == compute_schema_hash(b)

    def test_different_schemas_hash_differently(self) -> None:
        a = {"type": "object", "properties": {"a": {"type": "string"}}}
        b = {"type": "object", "properties": {"a": {"type": "integer"}}}
        assert compute_schema_hash(a) != compute_schema_hash(b)

    def test_returns_a_16_character_hex_string(self) -> None:
        digest = compute_schema_hash({"type": "object", "properties": {}})
        assert len(digest) == 16
        int(digest, 16)  # raises ValueError if not valid hex
