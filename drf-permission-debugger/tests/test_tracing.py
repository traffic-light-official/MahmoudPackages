"""Tests for :mod:`drf_permission_debugger.tracing`."""

from __future__ import annotations

from drf_permission_debugger.tracing import PermissionCheckResult, PermissionTrace


class TestPermissionCheckResult:
    def test_as_dict(self) -> None:
        result = PermissionCheckResult(
            permission_class="IsAuthenticated",
            granted=False,
            object_level=True,
            message="Nope.",
            code="denied",
        )
        assert result.as_dict() == {
            "permission_class": "IsAuthenticated",
            "granted": False,
            "object_level": True,
            "message": "Nope.",
            "code": "denied",
        }


class TestPermissionTrace:
    def test_denied_by_returns_the_first_denial(self) -> None:
        trace = PermissionTrace(
            [
                PermissionCheckResult("A", granted=True),
                PermissionCheckResult("B", granted=False, message="no"),
                PermissionCheckResult("C", granted=False, message="also no"),
            ]
        )
        denied = trace.denied_by
        assert denied is not None
        assert denied.permission_class == "B"

    def test_denied_by_returns_none_when_all_granted(self) -> None:
        trace = PermissionTrace([PermissionCheckResult("A", granted=True)])
        assert trace.denied_by is None

    def test_all_granted_true_when_every_result_granted(self) -> None:
        trace = PermissionTrace([PermissionCheckResult("A", granted=True)])
        assert trace.all_granted is True

    def test_all_granted_false_when_any_result_denied(self) -> None:
        trace = PermissionTrace(
            [PermissionCheckResult("A", granted=True), PermissionCheckResult("B", granted=False)]
        )
        assert trace.all_granted is False

    def test_all_granted_true_for_empty_trace(self) -> None:
        assert PermissionTrace([]).all_granted is True

    def test_as_dict_returns_a_list_of_dicts(self) -> None:
        trace = PermissionTrace([PermissionCheckResult("A", granted=True)])
        assert trace.as_dict() == [
            {
                "permission_class": "A",
                "granted": True,
                "object_level": False,
                "message": None,
                "code": None,
            }
        ]

    def test_as_header_value(self) -> None:
        trace = PermissionTrace(
            [PermissionCheckResult("A", granted=True), PermissionCheckResult("B", granted=False)]
        )
        assert trace.as_header_value() == "A=granted, B=denied"

    def test_default_construction_is_an_empty_trace(self) -> None:
        trace = PermissionTrace()
        assert trace.results == []
