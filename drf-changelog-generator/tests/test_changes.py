"""Tests for :mod:`drf_changelog_generator.changes`."""

from __future__ import annotations

from drf_changelog_generator.changes import Change, ChangeKind, SchemaDiff, Severity


def _change(kind: ChangeKind, severity: Severity, *, method: str | None = "get") -> Change:
    return Change(
        kind=kind, severity=severity, path="/articles/", method=method, location="", message="x"
    )


class TestChangeOperationLabel:
    def test_includes_method_when_present(self) -> None:
        change = _change(ChangeKind.ENDPOINT_ADDED, Severity.NON_BREAKING, method="get")

        assert change.operation_label == "GET /articles/"

    def test_is_just_the_path_without_a_method(self) -> None:
        change = _change(ChangeKind.ENDPOINT_ADDED, Severity.NON_BREAKING, method=None)

        assert change.operation_label == "/articles/"


class TestSchemaDiff:
    def test_breaking_changes_filters_by_severity(self) -> None:
        breaking = _change(ChangeKind.ENDPOINT_REMOVED, Severity.BREAKING)
        non_breaking = _change(ChangeKind.ENDPOINT_ADDED, Severity.NON_BREAKING)
        diff = SchemaDiff(changes=[breaking, non_breaking])

        assert diff.breaking_changes == [breaking]
        assert diff.non_breaking_changes == [non_breaking]

    def test_has_breaking_changes(self) -> None:
        assert SchemaDiff(
            changes=[_change(ChangeKind.ENDPOINT_REMOVED, Severity.BREAKING)]
        ).has_breaking_changes
        assert not SchemaDiff(
            changes=[_change(ChangeKind.ENDPOINT_ADDED, Severity.NON_BREAKING)]
        ).has_breaking_changes

    def test_is_empty(self) -> None:
        assert SchemaDiff(changes=[]).is_empty is True
        assert (
            SchemaDiff(changes=[_change(ChangeKind.ENDPOINT_ADDED, Severity.NON_BREAKING)]).is_empty
            is False
        )
