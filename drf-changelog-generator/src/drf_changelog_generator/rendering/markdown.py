"""Renders a schema diff as a Markdown changelog document."""

from __future__ import annotations

from drf_changelog_generator.changes import Change, SchemaDiff
from drf_changelog_generator.rendering.common import summarize


def render_markdown(diff: SchemaDiff, *, old_ref: str, new_ref: str) -> str:
    """Render ``diff`` as a Markdown document.

    Args:
        diff: The diff to render.
        old_ref: A label for the earlier version (a Git tag, branch, or
            file path).
        new_ref: A label for the later version.

    Returns:
        A Markdown document, terminated with a trailing newline.
    """
    summary = summarize(diff)
    lines: list[str] = [f"# API Changelog: `{old_ref}` -> `{new_ref}`", ""]

    if diff.is_empty:
        lines.append("No API changes detected.")
        return "\n".join(lines) + "\n"

    _add_section(lines, "Breaking Changes", summary.other_breaking)
    _add_section(lines, "Removed Endpoints", summary.removed_endpoints)
    _add_section(lines, "Deprecated Endpoints", summary.deprecated_endpoints)
    _add_section(lines, "Added Endpoints", summary.added_endpoints)
    _add_section(lines, "Non-Breaking Changes", summary.other_non_breaking)

    return "\n".join(lines).rstrip() + "\n"


def _add_section(lines: list[str], title: str, changes: list[Change]) -> None:
    if not changes:
        return
    lines.append(f"## {title}")
    lines.append("")
    for change in changes:
        lines.append(f"- `{change.operation_label}`: {change.message}")
    lines.append("")
