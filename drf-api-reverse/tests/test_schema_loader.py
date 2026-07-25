"""Tests for :mod:`drf_api_reverse.schema_loader`."""

from __future__ import annotations

from pathlib import Path

import pytest

from drf_api_reverse.exceptions import SchemaParseError
from drf_api_reverse.schema_loader import load_schema_file, parse_schema


class TestParseSchema:
    def test_parses_json(self) -> None:
        result = parse_schema('{"openapi": "3.0.3"}', suffix=".json")
        assert result == {"openapi": "3.0.3"}

    def test_parses_yaml(self) -> None:
        result = parse_schema("openapi: 3.0.3\npaths: {}\n", suffix=".yml")
        assert result == {"openapi": "3.0.3", "paths": {}}

    def test_parses_yaml_without_a_suffix_hint(self) -> None:
        result = parse_schema("openapi: 3.0.3\n")
        assert result == {"openapi": "3.0.3"}

    def test_json_is_also_valid_yaml_and_parses_either_way(self) -> None:
        result = parse_schema('{"openapi": "3.0.3"}')
        assert result == {"openapi": "3.0.3"}

    def test_raises_on_unparsable_text(self) -> None:
        with pytest.raises(SchemaParseError):
            parse_schema(":\n  - not: [valid, {", suffix=".yml")

    def test_raises_when_top_level_is_not_a_mapping(self) -> None:
        with pytest.raises(SchemaParseError, match="not a mapping"):
            parse_schema("- just\n- a\n- list\n")


class TestLoadSchemaFile:
    def test_loads_a_yaml_file(self, tmp_path: Path) -> None:
        path = tmp_path / "schema.yml"
        path.write_text("openapi: 3.0.3\n", encoding="utf-8")

        assert load_schema_file(path) == {"openapi": "3.0.3"}

    def test_loads_a_json_file(self, tmp_path: Path) -> None:
        path = tmp_path / "schema.json"
        path.write_text('{"openapi": "3.0.3"}', encoding="utf-8")

        assert load_schema_file(path) == {"openapi": "3.0.3"}

    def test_raises_for_a_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(OSError):
            load_schema_file(tmp_path / "does-not-exist.yml")
