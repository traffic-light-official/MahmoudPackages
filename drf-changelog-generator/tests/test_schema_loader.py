"""Tests for :mod:`drf_changelog_generator.schema_loader`."""

from __future__ import annotations

from pathlib import Path

import pytest

from drf_changelog_generator.exceptions import SchemaParseError
from drf_changelog_generator.schema_loader import load_schema_file, parse_schema


class TestParseSchema:
    def test_parses_json_by_suffix(self) -> None:
        result = parse_schema('{"openapi": "3.0.3"}', suffix=".json")

        assert result == {"openapi": "3.0.3"}

    def test_parses_json_by_sniffing_content(self) -> None:
        result = parse_schema('{"openapi": "3.0.3"}')

        assert result == {"openapi": "3.0.3"}

    def test_parses_yaml_by_suffix(self) -> None:
        result = parse_schema("openapi: 3.0.3\ninfo:\n  title: Test\n", suffix=".yml")

        assert result == {"openapi": "3.0.3", "info": {"title": "Test"}}

    def test_parses_yaml_when_no_suffix_and_not_json_like(self) -> None:
        result = parse_schema("openapi: 3.0.3\n")

        assert result == {"openapi": "3.0.3"}

    def test_raises_on_invalid_json(self) -> None:
        with pytest.raises(SchemaParseError):
            parse_schema("{not valid json", suffix=".json")

    def test_raises_on_invalid_yaml(self) -> None:
        with pytest.raises(SchemaParseError):
            parse_schema("key: [unterminated", suffix=".yml")

    def test_raises_when_top_level_is_not_a_mapping(self) -> None:
        with pytest.raises(SchemaParseError, match="mapping"):
            parse_schema("[1, 2, 3]", suffix=".yml")


class TestLoadSchemaFile:
    def test_loads_a_yaml_file(self, tmp_path: Path) -> None:
        schema_file = tmp_path / "schema.yml"
        schema_file.write_text("openapi: 3.0.3\n", encoding="utf-8")

        assert load_schema_file(schema_file) == {"openapi": "3.0.3"}

    def test_loads_a_json_file(self, tmp_path: Path) -> None:
        schema_file = tmp_path / "schema.json"
        schema_file.write_text('{"openapi": "3.0.3"}', encoding="utf-8")

        assert load_schema_file(schema_file) == {"openapi": "3.0.3"}

    def test_raises_for_a_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_schema_file(tmp_path / "does-not-exist.yml")
