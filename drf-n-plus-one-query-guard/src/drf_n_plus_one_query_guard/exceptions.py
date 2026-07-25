"""Exceptions raised by :mod:`drf_n_plus_one_query_guard`."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from drf_n_plus_one_query_guard.tracker import Violation


class NPlusOneGuardError(Exception):
    """Base class for every exception raised by this package."""


class NPlusOneDetectedError(NPlusOneGuardError):
    """Raised in ``"raise"`` mode when a suspected N+1 pattern is found."""

    def __init__(self, violations: list[Violation]) -> None:
        self.violations = violations
        summary = "; ".join(
            f"{v.count}x {v.fingerprint!r} (first seen at {v.call_site})" for v in violations
        )
        super().__init__(f"Suspected N+1 quer{'y' if len(violations) == 1 else 'ies'}: {summary}")
