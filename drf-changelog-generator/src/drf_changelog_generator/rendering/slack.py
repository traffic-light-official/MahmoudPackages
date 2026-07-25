"""Renders a schema diff as Slack Block Kit blocks, and can post them to a webhook."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from drf_changelog_generator.changes import Change, SchemaDiff
from drf_changelog_generator.exceptions import ChangelogGeneratorError
from drf_changelog_generator.rendering.common import summarize

_MAX_ITEMS_PER_SECTION = 20


def render_slack_blocks(diff: SchemaDiff, *, old_ref: str, new_ref: str) -> list[dict[str, Any]]:
    """Render ``diff`` as a list of Slack Block Kit blocks.

    Pass the result as the ``"blocks"`` field of a Slack ``chat.postMessage``
    payload or incoming-webhook payload.

    Args:
        diff: The diff to render.
        old_ref: A label for the earlier version.
        new_ref: A label for the later version.

    Returns:
        A list of Block Kit block objects.
    """
    summary = summarize(diff)
    blocks: list[dict[str, Any]] = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"API Changelog: {old_ref} -> {new_ref}"},
        }
    ]

    if diff.is_empty:
        blocks.append(_section_block("_No API changes detected._"))
        return blocks

    blocks.extend(_change_section(":warning: Breaking Changes", summary.other_breaking))
    blocks.extend(_change_section(":x: Removed Endpoints", summary.removed_endpoints))
    blocks.extend(_change_section(":hourglass: Deprecated Endpoints", summary.deprecated_endpoints))
    blocks.extend(_change_section(":sparkles: Added Endpoints", summary.added_endpoints))
    blocks.extend(
        _change_section(":information_source: Non-Breaking Changes", summary.other_non_breaking)
    )
    return blocks


def _change_section(title: str, changes: list[Change]) -> list[dict[str, Any]]:
    if not changes:
        return []
    shown = changes[:_MAX_ITEMS_PER_SECTION]
    lines = [f"- `{c.operation_label}`: {c.message}" for c in shown]
    if len(changes) > len(shown):
        lines.append(f"_...and {len(changes) - len(shown)} more._")
    return [
        {"type": "divider"},
        _section_block(f"*{title}*\n" + "\n".join(lines)),
    ]


def _section_block(text: str) -> dict[str, Any]:
    return {"type": "section", "text": {"type": "mrkdwn", "text": text}}


def post_to_slack_webhook(
    webhook_url: str, blocks: list[dict[str, Any]], *, timeout: float = 5.0
) -> None:
    """POST ``blocks`` to a Slack incoming webhook URL.

    Args:
        webhook_url: The Slack incoming webhook URL.
        blocks: Block Kit blocks, typically from :func:`render_slack_blocks`.
        timeout: Request timeout, in seconds.

    Raises:
        ChangelogGeneratorError: If the webhook request fails or Slack
            responds with a non-2xx status.
    """
    payload = json.dumps({"blocks": blocks}).encode("utf-8")
    request = urllib.request.Request(
        webhook_url, data=payload, method="POST", headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if response.status >= 300:
                raise ChangelogGeneratorError(
                    f"Slack webhook responded with status {response.status}."
                )
    except urllib.error.URLError as exc:
        raise ChangelogGeneratorError(f"Failed to post to Slack webhook: {exc}") from exc
