"""Tests for :mod:`drf_changelog_generator.rendering.common`."""

from __future__ import annotations

from drf_changelog_generator.changes import Change, ChangeKind, SchemaDiff, Severity
from drf_changelog_generator.rendering.common import summarize


def _change(kind: ChangeKind, severity: Severity) -> Change:
    return Change(kind=kind, severity=severity, path="/x/", method="get", location="", message="m")


class TestSummarize:
    def test_partitions_every_kind_into_its_own_bucket(self) -> None:
        diff = SchemaDiff(
            changes=[
                _change(ChangeKind.ENDPOINT_ADDED, Severity.NON_BREAKING),
                _change(ChangeKind.ENDPOINT_REMOVED, Severity.BREAKING),
                _change(ChangeKind.ENDPOINT_DEPRECATED, Severity.NON_BREAKING),
                _change(ChangeKind.ENDPOINT_UNDEPRECATED, Severity.NON_BREAKING),
                _change(ChangeKind.PARAMETER_REMOVED, Severity.BREAKING),
                _change(ChangeKind.REQUEST_FIELD_ADDED, Severity.NON_BREAKING),
            ]
        )

        summary = summarize(diff)

        assert len(summary.added_endpoints) == 1
        assert len(summary.removed_endpoints) == 1
        assert len(summary.deprecated_endpoints) == 2
        assert len(summary.other_breaking) == 1
        assert len(summary.other_non_breaking) == 1

    def test_is_empty(self) -> None:
        assert summarize(SchemaDiff(changes=[])).is_empty is True

    def test_is_not_empty_with_any_change(self) -> None:
        diff = SchemaDiff(changes=[_change(ChangeKind.ENDPOINT_ADDED, Severity.NON_BREAKING)])

        assert summarize(diff).is_empty is False

    def test_no_change_appears_in_two_buckets(self) -> None:
        diff = SchemaDiff(
            changes=[
                _change(ChangeKind.ENDPOINT_ADDED, Severity.NON_BREAKING),
                _change(ChangeKind.ENDPOINT_REMOVED, Severity.BREAKING),
            ]
        )

        summary = summarize(diff)

        assert summary.other_breaking == []
        assert summary.other_non_breaking == []
