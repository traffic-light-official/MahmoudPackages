"""Tests for drf_contract_test.changes."""

from __future__ import annotations

from drf_contract_test.changes import Change, DiffResult, Severity


def _change(severity: Severity, kind: str = "x") -> Change:
    return Change(severity=severity, operation="GET /x/", location="x", kind=kind, message="msg")


class TestDiffResult:
    def test_empty_result_has_no_changes(self) -> None:
        result = DiffResult()
        assert result.changes == ()
        assert result.breaking_changes == ()
        assert result.safe_changes == ()
        assert result.info_changes == ()
        assert result.has_breaking_changes is False

    def test_partitions_changes_by_severity(self) -> None:
        changes = (
            _change(Severity.BREAKING, "a"),
            _change(Severity.SAFE, "b"),
            _change(Severity.INFO, "c"),
            _change(Severity.BREAKING, "d"),
        )
        result = DiffResult(changes=changes)
        assert [c.kind for c in result.breaking_changes] == ["a", "d"]
        assert [c.kind for c in result.safe_changes] == ["b"]
        assert [c.kind for c in result.info_changes] == ["c"]
        assert result.has_breaking_changes is True

    def test_has_breaking_changes_false_without_any_breaking(self) -> None:
        result = DiffResult(changes=(_change(Severity.SAFE), _change(Severity.INFO)))
        assert result.has_breaking_changes is False


class TestSeverity:
    def test_is_a_str_enum(self) -> None:
        assert Severity.BREAKING.value == "breaking"
        assert Severity.SAFE.value == "safe"
        assert Severity.INFO.value == "info"
        assert isinstance(Severity.BREAKING, str)


class TestChange:
    def test_is_frozen(self) -> None:
        change = _change(Severity.BREAKING)
        try:
            change.kind = "y"  # type: ignore[misc]
        except (AttributeError, TypeError):
            pass
        else:
            raise AssertionError("Change should be immutable")
