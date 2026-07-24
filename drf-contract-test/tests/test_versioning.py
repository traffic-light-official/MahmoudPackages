"""Tests for drf_contract_test.versioning."""

from __future__ import annotations

from drf_contract_test.changes import Change, DiffResult, Severity
from drf_contract_test.schema import Schema
from drf_contract_test.versioning import check_version_bump


def _schema(version: str) -> Schema:
    return Schema({"info": {"version": version}, "paths": {}})


def _breaking_diff() -> DiffResult:
    return DiffResult(
        changes=(Change(Severity.BREAKING, "GET /x/", "x", "field_removed", "removed"),)
    )


def _safe_diff() -> DiffResult:
    return DiffResult(changes=(Change(Severity.SAFE, "GET /x/", "x", "field_added", "added"),))


class TestNoBreakingChanges:
    def test_ok_regardless_of_version(self) -> None:
        result = check_version_bump(_schema("1.0.0"), _schema("1.0.0"), _safe_diff())
        assert result.ok is True


class TestSimpleVersionBump:
    def test_fails_when_version_unchanged(self) -> None:
        result = check_version_bump(_schema("1.0.0"), _schema("1.0.0"), _breaking_diff())
        assert result.ok is False
        assert "not bumped" in result.message

    def test_passes_when_version_changed_at_all(self) -> None:
        result = check_version_bump(_schema("1.0.0"), _schema("1.0.1"), _breaking_diff())
        assert result.ok is True


class TestMajorVersionBump:
    def test_fails_on_minor_bump_only(self) -> None:
        result = check_version_bump(
            _schema("1.0.0"), _schema("1.1.0"), _breaking_diff(), require_major_bump=True
        )
        assert result.ok is False

    def test_passes_on_major_bump(self) -> None:
        result = check_version_bump(
            _schema("1.0.0"), _schema("2.0.0"), _breaking_diff(), require_major_bump=True
        )
        assert result.ok is True

    def test_fails_on_major_downgrade(self) -> None:
        result = check_version_bump(
            _schema("2.0.0"), _schema("1.0.0"), _breaking_diff(), require_major_bump=True
        )
        assert result.ok is False

    def test_tolerates_leading_v(self) -> None:
        result = check_version_bump(
            _schema("v1.2.3"), _schema("v2.0.0"), _breaking_diff(), require_major_bump=True
        )
        assert result.ok is True

    def test_falls_back_to_string_comparison_when_unparseable(self) -> None:
        result = check_version_bump(
            _schema("release-a"), _schema("release-b"), _breaking_diff(), require_major_bump=True
        )
        assert result.ok is True
        assert "Could not parse" in result.message

    def test_falls_back_and_fails_when_unparseable_and_unchanged(self) -> None:
        result = check_version_bump(
            _schema("release-a"), _schema("release-a"), _breaking_diff(), require_major_bump=True
        )
        assert result.ok is False
