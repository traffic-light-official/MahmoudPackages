"""Loads an OpenAPI schema document from JSON or YAML text."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from drf_changelog_generator.exceptions import SchemaParseError


def load_schema_file(path: str | Path) -> dict[str, Any]:
    """Load and parse an OpenAPI schema from a local file.

    Args:
        path: Path to a ``.json``, ``.yml``, or ``.yaml`` schema file.

    Returns:
        The parsed schema as a plain dict.

    Raises:
        SchemaParseError: If the file cannot be parsed as JSON or YAML.
        FileNotFoundError: If ``path`` does not exist.
    """
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    return parse_schema(text, suffix=file_path.suffix)


def parse_schema(text: str, *, suffix: str = "") -> dict[str, Any]:
    """Parse OpenAPI schema text as JSON or YAML.

    Args:
        text: The raw schema document text.
        suffix: A filename suffix hint (``".json"``, ``".yml"``, ...).
            When empty or unrecognized, the content is sniffed: text
            starting with ``{`` is parsed as JSON, otherwise as YAML
            (a superset that also accepts JSON, so this is a safe
            fallback either way).

    Returns:
        The parsed schema as a plain dict.

    Raises:
        SchemaParseError: If the text cannot be parsed as JSON or YAML,
            or does not parse to a mapping at the top level.
    """
    try:
        if suffix.lower() == ".json" or text.lstrip().startswith("{"):
            parsed = json.loads(text)
        else:
            parsed = yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise SchemaParseError(f"Could not parse schema document: {exc}") from exc

    if not isinstance(parsed, dict):
        raise SchemaParseError(
            "Schema document must parse to a mapping at the top level, "
            f"got {type(parsed).__name__}."
        )
    return parsed
