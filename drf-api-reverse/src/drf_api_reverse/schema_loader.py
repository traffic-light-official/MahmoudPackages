"""Parses an OpenAPI document from a file or raw text, JSON or YAML."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from drf_api_reverse.exceptions import SchemaParseError


def load_schema_file(path: str | Path) -> dict[str, Any]:
    """Load and parse an OpenAPI schema file.

    Args:
        path: Path to a JSON or YAML OpenAPI document.

    Returns:
        The parsed schema as a plain dict.

    Raises:
        SchemaParseError: If the file's content cannot be parsed as
            JSON or YAML, or does not parse to a mapping.
        OSError: If the file cannot be read.
    """
    path = Path(path)
    return parse_schema(path.read_text(encoding="utf-8"), suffix=path.suffix)


def parse_schema(text: str, *, suffix: str = "") -> dict[str, Any]:
    """Parse OpenAPI schema text as JSON or YAML.

    Args:
        text: The raw file content.
        suffix: The source file's extension (e.g. ``".json"``), used as a
            hint only - both formats are attempted regardless.

    Returns:
        The parsed schema as a plain dict.

    Raises:
        SchemaParseError: If ``text`` cannot be parsed as JSON or YAML,
            or does not parse to a mapping.
    """
    parsers = (
        (_parse_json, _parse_yaml) if suffix.lower() in {".json"} else (_parse_yaml, _parse_json)
    )
    errors: list[str] = []
    for parser in parsers:
        try:
            document = parser(text)
        except (json.JSONDecodeError, yaml.YAMLError) as exc:
            errors.append(str(exc))
            continue
        if not isinstance(document, dict):
            kind = type(document).__name__
            errors.append(f"Parsed successfully but the top level is a {kind}, not a mapping.")
            continue
        return document
    raise SchemaParseError(f"Could not parse schema as JSON or YAML: {'; '.join(errors)}")


def _parse_json(text: str) -> Any:
    return json.loads(text)


def _parse_yaml(text: str) -> Any:
    return yaml.safe_load(text)
