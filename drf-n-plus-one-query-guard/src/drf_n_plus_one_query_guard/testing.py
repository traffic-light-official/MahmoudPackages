"""Test-time helpers - a plain assertion context manager, no Django settings required.

Deliberately independent of the ``N_PLUS_ONE_GUARD`` Django setting:
tests should be explicit about the threshold they're asserting, not
dependent on ambient project configuration that could change under
them.
"""

from __future__ import annotations

import re
from types import TracebackType
from typing import TYPE_CHECKING

from drf_n_plus_one_query_guard.tracker import QueryTracker, Violation

if TYPE_CHECKING:
    from collections.abc import Sequence


class _NPlusOneAssertion:
    """The context manager object returned by :func:`assert_no_n_plus_one`."""

    def __init__(self, *, threshold: int, ignore_patterns: Sequence[str]) -> None:
        self.threshold = threshold
        self._ignore_patterns = tuple(re.compile(pattern) for pattern in ignore_patterns)
        self._tracker = QueryTracker()
        self.violations: list[Violation] = []

    def __enter__(self) -> _NPlusOneAssertion:
        self._tracker.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._tracker.__exit__(exc_type, exc_value, traceback)
        if exc_type is not None:
            # Let a real test failure/error propagate as-is; don't pile a
            # second, unrelated AssertionError on top of it.
            return
        self.violations = self._tracker.violations(
            threshold=self.threshold, ignore_patterns=self._ignore_patterns
        )
        if self.violations:
            summary = "\n".join(
                f"  {violation.count}x {violation.fingerprint!r} (first at {violation.call_site})"
                for violation in self.violations
            )
            raise AssertionError(f"Suspected N+1 queries detected:\n{summary}")


def assert_no_n_plus_one(
    *, threshold: int = 2, ignore_patterns: Sequence[str] = ()
) -> _NPlusOneAssertion:
    """Fail the test if any query fingerprint repeats ``threshold`` times.

    Args:
        threshold: The minimum number of occurrences of an identically-
            shaped query for it to be reported. Defaults to ``2`` (any
            repeat at all).
        ignore_patterns: Regular expressions (matched via ``re.search``
            against the normalized SQL); a query matching any of them is
            never counted.

    Returns:
        A context manager. On exit, raises :class:`AssertionError` if
        any query fingerprint repeated at least ``threshold`` times.
        Read ``.violations`` afterward (e.g. in a fixture's teardown)
        for the full detail rather than only the exception message.

    Example:
        .. code-block:: python

            def test_article_list_has_no_n_plus_one(api_client):
                with assert_no_n_plus_one():
                    api_client.get("/articles/")
    """
    return _NPlusOneAssertion(threshold=threshold, ignore_patterns=ignore_patterns)
