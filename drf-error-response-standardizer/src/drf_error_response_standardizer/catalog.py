"""Error catalog generation.

Produces a machine-readable and human-readable catalog of every problem
type an API can return, derived from a
:class:`~drf_error_response_standardizer.registry.ProblemRegistry`. Run it in
CI via the ``generate_error_catalog`` management command to keep
error-response documentation in sync with what the API actually returns.
"""

from __future__ import annotations

import json
from typing import Any

from drf_error_response_standardizer.registry import ProblemRegistry, default_registry
from drf_error_response_standardizer.settings import get_setting


def build_catalog(registry: ProblemRegistry | None = None) -> list[dict[str, Any]]:
    """Build the error catalog as a list of plain dicts, sorted by ``code``.

    Args:
        registry: The registry to introspect. Defaults to
            :data:`~drf_error_response_standardizer.registry.default_registry`.

    Returns:
        A list of dicts, one per distinct
        :class:`~drf_error_response_standardizer.codes.ErrorType`, each with
        ``code``, ``title``, ``status``, and ``type`` (the fully qualified
        type URI, honoring the ``TYPE_BASE_URI`` setting).
    """
    active_registry = registry or default_registry
    base_uri = get_setting("TYPE_BASE_URI")
    entries = []
    for error_type in active_registry.all_error_types():
        type_uri = f"{base_uri}{error_type.slug}" if base_uri else "about:blank"
        entries.append(
            {
                "code": error_type.code,
                "title": error_type.title,
                "status": error_type.status,
                "type": type_uri,
            }
        )
    return sorted(entries, key=lambda entry: str(entry["code"]))


def render_json(catalog: list[dict[str, Any]]) -> str:
    """Render a catalog (from :func:`build_catalog`) as pretty-printed JSON.

    Args:
        catalog: The catalog entries to render.

    Returns:
        A JSON string, terminated with a trailing newline.
    """
    return json.dumps(catalog, indent=2, sort_keys=True) + "\n"


def render_markdown(catalog: list[dict[str, Any]]) -> str:
    """Render a catalog (from :func:`build_catalog`) as a Markdown table.

    Args:
        catalog: The catalog entries to render.

    Returns:
        A Markdown document with a ``# Error Catalog`` heading followed by
        a table of every entry.
    """
    lines = [
        "# Error Catalog",
        "",
        "| Code | Title | HTTP Status | Type URI |",
        "| --- | --- | --- | --- |",
    ]
    for entry in catalog:
        lines.append(
            f"| `{entry['code']}` | {entry['title']} | {entry['status']} | `{entry['type']}` |"
        )
    lines.append("")
    return "\n".join(lines)
