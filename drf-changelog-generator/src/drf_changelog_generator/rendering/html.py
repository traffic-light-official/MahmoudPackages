"""Renders a schema diff as a self-contained HTML changelog document."""

from __future__ import annotations

from html import escape

from drf_changelog_generator.changes import Change, SchemaDiff
from drf_changelog_generator.rendering.common import summarize

_STYLE = """
body {
  font-family: -apple-system, Arial, sans-serif;
  max-width: 800px;
  margin: 2rem auto;
  line-height: 1.5;
  color: #1a1a1a;
}
h1 { font-size: 1.5rem; }
h2 {
  font-size: 1.15rem;
  margin-top: 2rem;
  border-bottom: 1px solid #ddd;
  padding-bottom: 0.25rem;
}
ul { padding-left: 1.25rem; }
code {
  background: #f3f3f3;
  padding: 0.1rem 0.3rem;
  border-radius: 3px;
  font-size: 0.9em;
}
.breaking h2 { color: #b3261e; }
.empty { color: #666; font-style: italic; }
"""


def render_html(diff: SchemaDiff, *, old_ref: str, new_ref: str) -> str:
    """Render ``diff`` as a self-contained HTML document.

    Args:
        diff: The diff to render.
        old_ref: A label for the earlier version.
        new_ref: A label for the later version.

    Returns:
        A complete, styled HTML document.
    """
    summary = summarize(diff)
    title = f"API Changelog: {escape(old_ref)} -&gt; {escape(new_ref)}"
    body_parts: list[str] = [f"<h1>{title}</h1>"]

    if diff.is_empty:
        body_parts.append('<p class="empty">No API changes detected.</p>')
    else:
        body_parts.append(
            _section("Breaking Changes", summary.other_breaking, css_class="breaking")
        )
        body_parts.append(
            _section("Removed Endpoints", summary.removed_endpoints, css_class="breaking")
        )
        body_parts.append(_section("Deprecated Endpoints", summary.deprecated_endpoints))
        body_parts.append(_section("Added Endpoints", summary.added_endpoints))
        body_parts.append(_section("Non-Breaking Changes", summary.other_non_breaking))

    body = "\n".join(part for part in body_parts if part)
    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        f"<title>{title}</title>\n"
        f"<style>{_STYLE}</style>\n"
        "</head>\n"
        f"<body>\n{body}\n</body>\n"
        "</html>\n"
    )


def _section(title: str, changes: list[Change], *, css_class: str = "") -> str:
    if not changes:
        return ""
    items = "\n".join(
        f"<li><code>{escape(c.operation_label)}</code>: {escape(c.message)}</li>" for c in changes
    )
    class_attr = f' class="{css_class}"' if css_class else ""
    return f"<div{class_attr}>\n<h2>{escape(title)}</h2>\n<ul>\n{items}\n</ul>\n</div>"
