"""Tests for :mod:`drf_changelog_generator.rendering.slack`."""

from __future__ import annotations

import json
from http.client import HTTPResponse
from unittest.mock import MagicMock, patch

import pytest

from drf_changelog_generator.changes import Change, ChangeKind, SchemaDiff, Severity
from drf_changelog_generator.diffing.engine import diff_schemas
from drf_changelog_generator.exceptions import ChangelogGeneratorError
from drf_changelog_generator.rendering.slack import post_to_slack_webhook, render_slack_blocks


class TestRenderSlackBlocks:
    def test_empty_diff_has_a_header_and_a_message(self) -> None:
        blocks = render_slack_blocks(SchemaDiff(changes=[]), old_ref="v1.0.0", new_ref="v1.1.0")

        assert blocks[0]["type"] == "header"
        assert "v1.0.0" in blocks[0]["text"]["text"]
        assert any("No API changes detected" in b.get("text", {}).get("text", "") for b in blocks)

    def test_rich_diff_produces_a_section_per_category(
        self, old_schema: dict, new_schema: dict
    ) -> None:
        diff = diff_schemas(old_schema, new_schema)

        blocks = render_slack_blocks(diff, old_ref="v1.0.0", new_ref="v1.1.0")

        section_texts = " ".join(b["text"]["text"] for b in blocks if b["type"] == "section")
        assert "Breaking Changes" in section_texts
        assert "Added Endpoints" in section_texts
        assert "Deprecated Endpoints" in section_texts

    def test_truncates_long_sections(self) -> None:
        changes = [
            Change(
                kind=ChangeKind.ENDPOINT_ADDED,
                severity=Severity.NON_BREAKING,
                path=f"/x{i}/",
                method="get",
                location="",
                message=f"Added GET /x{i}/",
            )
            for i in range(30)
        ]
        diff = SchemaDiff(changes=changes)

        blocks = render_slack_blocks(diff, old_ref="a", new_ref="b")

        section_texts = " ".join(b["text"]["text"] for b in blocks if b["type"] == "section")
        assert "...and 10 more." in section_texts


class TestPostToSlackWebhook:
    def test_posts_the_blocks_as_json(self) -> None:
        fake_response = MagicMock(spec=HTTPResponse)
        fake_response.status = 200
        fake_response.__enter__ = MagicMock(return_value=fake_response)
        fake_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=fake_response) as urlopen:
            post_to_slack_webhook("https://hooks.slack.example/webhook", [{"type": "header"}])

        request = urlopen.call_args[0][0]
        assert json.loads(request.data) == {"blocks": [{"type": "header"}]}

    def test_raises_on_non_2xx_response(self) -> None:
        fake_response = MagicMock(spec=HTTPResponse)
        fake_response.status = 500
        fake_response.__enter__ = MagicMock(return_value=fake_response)
        fake_response.__exit__ = MagicMock(return_value=False)

        with (
            patch("urllib.request.urlopen", return_value=fake_response),
            pytest.raises(ChangelogGeneratorError, match="status 500"),
        ):
            post_to_slack_webhook("https://hooks.slack.example/webhook", [])

    def test_raises_on_connection_failure(self) -> None:
        import urllib.error

        with (
            patch("urllib.request.urlopen", side_effect=urllib.error.URLError("refused")),
            pytest.raises(ChangelogGeneratorError, match="Failed to post"),
        ):
            post_to_slack_webhook("https://hooks.slack.example/webhook", [])
