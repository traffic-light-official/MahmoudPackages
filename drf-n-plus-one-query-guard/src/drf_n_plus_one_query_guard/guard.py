"""The high-level, settings-aware N+1 guard context manager."""

from __future__ import annotations

import logging
import re
from types import TracebackType

from drf_n_plus_one_query_guard.exceptions import NPlusOneDetectedError
from drf_n_plus_one_query_guard.settings import get_setting
from drf_n_plus_one_query_guard.tracker import QueryTracker, Violation


class NPlusOneGuard:
    """Tracks queries for one scope and dispatches on exit per ``MODE``.

    Usage:
        >>> with NPlusOneGuard() as guard:
        ...     pass  # code that may execute queries
        >>> guard.violations
        []

    ``MODE="raise"`` raises :class:`~drf_n_plus_one_query_guard.exceptions.NPlusOneDetectedError`
    on `__exit__` if any violation was found (and the body did not
    already raise - see :meth:`__exit__`). ``MODE="warn"`` logs each
    violation instead. ``MODE="report"`` does neither; read
    ``guard.violations`` yourself afterward.
    """

    def __init__(
        self,
        *,
        threshold: int | None = None,
        mode: str | None = None,
    ) -> None:
        self.threshold = threshold if threshold is not None else get_setting("THRESHOLD")
        self.mode = mode if mode is not None else get_setting("MODE")
        self._ignore_patterns = tuple(
            re.compile(pattern) for pattern in get_setting("IGNORE_PATTERNS")
        )
        self._tracker = QueryTracker()
        self.violations: list[Violation] = []

    def __enter__(self) -> NPlusOneGuard:
        self._tracker.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._tracker.__exit__(exc_type, exc_value, traceback)
        self.violations = self._tracker.violations(
            threshold=self.threshold, ignore_patterns=self._ignore_patterns
        )
        if not self.violations or exc_type is not None:
            # An exception already propagating from the guarded block takes
            # priority - don't mask it with a violation report/raise.
            return
        self._dispatch()

    def _dispatch(self) -> None:
        if self.mode == "raise":
            raise NPlusOneDetectedError(self.violations)
        if self.mode == "warn":
            logger = logging.getLogger(get_setting("LOGGER_NAME"))
            for violation in self.violations:
                logger.warning(
                    "Suspected N+1: %r executed %d times (first at %s)",
                    violation.fingerprint,
                    violation.count,
                    violation.call_site,
                )
        # mode == "report": nothing to do, .violations is already populated.
