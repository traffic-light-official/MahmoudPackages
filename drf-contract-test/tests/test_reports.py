"""Tests for drf_contract_test.reports."""

from __future__ import annotations

import json

from drf_contract_test.changes import Change, DiffResult, Severity
from drf_contract_test.reports import render_html, render_json, render_text
from drf_contract_test.versioning import VersionCheckResult


def _diff() -> DiffResult:
    return DiffResult(
        changes=(
            Change(
                Severity.BREAKING, "GET /x/", "x.properties.a", "field_removed", "field 'a' removed"
            ),
            Change(Severity.SAFE, "GET /x/", "x.properties.b", "field_added", "field 'b' added"),
        )
    )


class TestRenderText:
    def test_includes_every_change_and_summary(self) -> None:
        text = render_text(_diff())
        assert "BREAKING" in text
        assert "SAFE" in text
        assert "field 'a' removed" in text
        assert "1 breaking change(s), 1 safe change(s)." in text

    def test_includes_version_check_message_when_given(self) -> None:
        vc = VersionCheckResult(
            ok=False, message="version not bumped", baseline_version="1.0", current_version="1.0"
        )
        text = render_text(_diff(), version_check=vc)
        assert "version not bumped" in text

    def test_empty_diff_still_renders_summary(self) -> None:
        text = render_text(DiffResult())
        assert "0 breaking change(s), 0 safe change(s)." in text


class TestRenderJson:
    def test_produces_valid_json_with_expected_shape(self) -> None:
        payload = json.loads(render_json(_diff()))
        assert payload["summary"]["breaking_count"] == 1
        assert payload["summary"]["safe_count"] == 1
        assert payload["summary"]["has_breaking_changes"] is True
        assert len(payload["changes"]) == 2
        assert payload["changes"][0]["severity"] == "breaking"
        assert payload["changes"][0]["message"] == "field 'a' removed"

    def test_version_check_included_when_given(self) -> None:
        vc = VersionCheckResult(
            ok=True, message="ok", baseline_version="1.0", current_version="2.0"
        )
        payload = json.loads(render_json(_diff(), version_check=vc))
        assert payload["version_check"] == {
            "ok": True,
            "message": "ok",
            "baseline_version": "1.0",
            "current_version": "2.0",
        }

    def test_version_check_omitted_when_not_given(self) -> None:
        payload = json.loads(render_json(_diff()))
        assert "version_check" not in payload


class TestRenderHtml:
    def test_is_self_contained_html(self) -> None:
        html = render_html(_diff())
        assert html.strip().startswith("<!doctype html>")
        assert "<style>" in html  # inline CSS, no external stylesheet
        assert "field 'a' removed" in html
        assert "BREAKING" in html

    def test_summary_class_reflects_breaking_state(self) -> None:
        assert "summary fail" in render_html(_diff())
        safe_only = DiffResult(
            changes=(Change(Severity.SAFE, "GET /x/", "x", "field_added", "added"),)
        )
        assert "summary ok" in render_html(safe_only)

    def test_no_external_assets(self) -> None:
        html = render_html(_diff())
        assert "http://" not in html
        assert "https://" not in html
