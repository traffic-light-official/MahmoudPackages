"""Renders a schema diff as GitHub Release notes."""

from __future__ import annotations

from drf_changelog_generator.changes import Change, SchemaDiff
from drf_changelog_generator.rendering.common import summarize


def render_github_release_notes(
    diff: SchemaDiff, *, old_ref: str, new_ref: str, repo: str | None = None
) -> str:
    """Render ``diff`` as Markdown suitable for a GitHub Release body.

    Args:
        diff: The diff to render.
        old_ref: The earlier Git tag.
        new_ref: The later Git tag.
        repo: ``"owner/name"`` GitHub repository slug. When given, a
            "Full API Diff" comparison link is appended, in the
            same style GitHub's own auto-generated release notes use.

    Returns:
        A Markdown document, terminated with a trailing newline.
    """
    summary = summarize(diff)
    lines: list[str] = []

    if diff.is_empty:
        lines.append("No API changes in this release.")
    else:
        if summary.other_breaking or summary.removed_endpoints:
            lines.append("## :warning: Breaking API Changes")
            lines.append("")
            for change in [*summary.removed_endpoints, *summary.other_breaking]:
                lines.append(_bullet(change))
            lines.append("")

        if summary.deprecated_endpoints:
            lines.append("## Deprecated")
            lines.append("")
            for change in summary.deprecated_endpoints:
                lines.append(_bullet(change))
            lines.append("")

        if summary.added_endpoints:
            lines.append("## Added")
            lines.append("")
            for change in summary.added_endpoints:
                lines.append(_bullet(change))
            lines.append("")

        if summary.other_non_breaking:
            lines.append("## Other API Changes")
            lines.append("")
            for change in summary.other_non_breaking:
                lines.append(_bullet(change))
            lines.append("")

    if repo:
        lines.append(f"**Full API Diff**: https://github.com/{repo}/compare/{old_ref}...{new_ref}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _bullet(change: Change) -> str:
    return f"- `{change.operation_label}`: {change.message}"
