"""Rendering a :class:`~drf_contract_test.changes.DiffResult` as text, JSON, or HTML.

All three renderers accept the same inputs and produce a string — the CLI
writes it to stdout or a file; a CI system can archive the JSON/HTML as a
build artifact, or post the text version as a PR comment.
"""

from __future__ import annotations

import json
from typing import Any

from jinja2 import Template

from drf_contract_test.changes import Change, DiffResult
from drf_contract_test.versioning import VersionCheckResult

_HTML_TEMPLATE = Template(
    """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>API Contract Report</title>
<style>
  body { font-family: -apple-system, Segoe UI, sans-serif; margin: 2rem; color: #1a1a1a; }
  h1 { font-size: 1.4rem; }
  table { border-collapse: collapse; width: 100%; margin-top: 1rem; }
  th, td { text-align: left; padding: 0.5rem 0.75rem; border-bottom: 1px solid #ddd; font-size: 0.9rem; }
  th { background: #f5f5f5; }
  .breaking { color: #b00020; font-weight: 600; }
  .safe { color: #146c2e; }
  .info { color: #555; }
  .summary { margin: 1rem 0; padding: 0.75rem 1rem; border-radius: 6px; }
  .summary.fail { background: #fdecea; border: 1px solid #f5c2c0; }
  .summary.ok { background: #eaf7ee; border: 1px solid #bfe6cb; }
  code { background: #f0f0f0; padding: 0.1rem 0.3rem; border-radius: 3px; }
</style>
</head>
<body>
<h1>API Contract Report</h1>
<div class="summary {{ 'fail' if breaking_count else 'ok' }}">
  <strong>{{ breaking_count }}</strong> breaking change(s),
  <strong>{{ safe_count }}</strong> safe change(s).
  {% if version_check %}<br>{{ version_check.message }}{% endif %}
</div>
<table>
  <thead><tr><th>Severity</th><th>Operation</th><th>Location</th><th>Message</th></tr></thead>
  <tbody>
  {% for change in changes %}
    <tr>
      <td class="{{ change.severity.value }}">{{ change.severity.value|upper }}</td>
      <td>{{ change.operation or "-" }}</td>
      <td><code>{{ change.location or "-" }}</code></td>
      <td>{{ change.message }}</td>
    </tr>
  {% endfor %}
  </tbody>
</table>
</body>
</html>
"""
)


def render_text(diff: DiffResult, *, version_check: VersionCheckResult | None = None) -> str:
    """Render a plain-text report, suitable for terminal output or CI logs.

    Args:
        diff: The comparison result to render.
        version_check: An optional version-bump check result to include.

    Returns:
        A multi-line plain-text report.
    """
    lines: list[str] = []
    for change in diff.changes:
        lines.append(f"{change.severity.value.upper():8s} {change.operation or '-'} - {change.message}")
    lines.append("")
    lines.append(
        f"{len(diff.breaking_changes)} breaking change(s), {len(diff.safe_changes)} safe change(s)."
    )
    if version_check is not None:
        lines.append(version_check.message)
    return "\n".join(lines)


def render_json(diff: DiffResult, *, version_check: VersionCheckResult | None = None) -> str:
    """Render a machine-readable JSON report.

    Args:
        diff: The comparison result to render.
        version_check: An optional version-bump check result to include.

    Returns:
        A JSON string with ``changes``, ``summary``, and (if given)
        ``version_check`` keys.
    """
    payload: dict[str, Any] = {
        "changes": [_change_to_dict(c) for c in diff.changes],
        "summary": {
            "breaking_count": len(diff.breaking_changes),
            "safe_count": len(diff.safe_changes),
            "info_count": len(diff.info_changes),
            "has_breaking_changes": diff.has_breaking_changes,
        },
    }
    if version_check is not None:
        payload["version_check"] = {
            "ok": version_check.ok,
            "message": version_check.message,
            "baseline_version": version_check.baseline_version,
            "current_version": version_check.current_version,
        }
    return json.dumps(payload, indent=2)


def render_html(diff: DiffResult, *, version_check: VersionCheckResult | None = None) -> str:
    """Render an HTML report, suitable for a CI artifact or dashboard.

    Args:
        diff: The comparison result to render.
        version_check: An optional version-bump check result to include.

    Returns:
        A self-contained HTML document (inline CSS, no external assets).
    """
    return _HTML_TEMPLATE.render(
        changes=diff.changes,
        breaking_count=len(diff.breaking_changes),
        safe_count=len(diff.safe_changes),
        version_check=version_check,
    )


def _change_to_dict(change: Change) -> dict[str, Any]:
    return {
        "severity": change.severity.value,
        "operation": change.operation,
        "location": change.location,
        "kind": change.kind,
        "message": change.message,
    }
