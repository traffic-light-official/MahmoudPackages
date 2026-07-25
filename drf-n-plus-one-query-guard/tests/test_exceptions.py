"""Tests for :mod:`drf_n_plus_one_query_guard.exceptions`."""

from __future__ import annotations

from drf_n_plus_one_query_guard.exceptions import NPlusOneDetectedError, NPlusOneGuardError
from drf_n_plus_one_query_guard.tracker import Violation


class TestNPlusOneDetectedError:
    def test_is_a_guard_error(self) -> None:
        assert issubclass(NPlusOneDetectedError, NPlusOneGuardError)

    def test_message_singular_for_one_violation(self) -> None:
        violation = Violation(
            fingerprint="SELECT 1", count=2, sample_sql="SELECT 1", call_site="x.py:1"
        )
        error = NPlusOneDetectedError([violation])
        assert "N+1 query:" in str(error)
        assert "N+1 queries:" not in str(error)

    def test_message_plural_for_multiple_violations(self) -> None:
        violations = [
            Violation(fingerprint="SELECT 1", count=2, sample_sql="SELECT 1", call_site="x.py:1"),
            Violation(fingerprint="SELECT 2", count=3, sample_sql="SELECT 2", call_site="y.py:2"),
        ]
        error = NPlusOneDetectedError(violations)
        assert "N+1 queries:" in str(error)

    def test_stores_the_violations(self) -> None:
        violation = Violation(
            fingerprint="SELECT 1", count=2, sample_sql="SELECT 1", call_site="x.py:1"
        )
        error = NPlusOneDetectedError([violation])
        assert error.violations == [violation]

    def test_message_includes_count_and_call_site(self) -> None:
        violation = Violation(
            fingerprint="SELECT 1", count=7, sample_sql="SELECT 1", call_site="views.py:99"
        )
        error = NPlusOneDetectedError([violation])
        assert "7x" in str(error)
        assert "views.py:99" in str(error)
