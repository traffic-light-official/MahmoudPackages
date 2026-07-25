"""Captures every SQL query executed within a scope and groups repeats.

Uses Django's own public instrumentation hook,
``connection.execute_wrapper()`` (stable API since Django 3.0), rather
than monkeypatching or reading ``connection.queries`` - this works
regardless of ``settings.DEBUG`` and on every configured database alias,
not just ``default``.
"""

from __future__ import annotations

import re
import traceback
from contextlib import ExitStack
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from django.db import connections

from drf_n_plus_one_query_guard.fingerprint import normalize_sql

if TYPE_CHECKING:
    from collections.abc import Sequence
    from types import TracebackType

_OWN_PACKAGE_DIR = str(Path(__file__).resolve().parent).replace("\\", "/")
_LIBRARY_MARKERS = ("/site-packages/", "/django/", "/rest_framework/")


@dataclass(frozen=True, slots=True)
class QueryEvent:
    """One executed SQL statement, as captured by :class:`QueryTracker`."""

    sql: str
    """The raw, parameterized SQL text (placeholders, not literal values)."""

    fingerprint: str
    """``sql`` after :func:`~drf_n_plus_one_query_guard.fingerprint.normalize_sql`."""

    alias: str
    """The database alias this query ran against (e.g. ``"default"``)."""

    call_site: str
    """The first non-library stack frame at the time of execution, as
    ``"<filename>:<lineno>"``, or ``"<unknown>"`` if none was found."""


@dataclass(frozen=True, slots=True)
class Violation:
    """A query fingerprint that repeated at least the configured threshold."""

    fingerprint: str
    count: int
    sample_sql: str
    call_site: str
    """The first call site at which this fingerprint was seen."""
    call_sites: tuple[str, ...] = field(default_factory=tuple)
    """Every distinct call site this fingerprint was seen at, in order."""


class QueryTracker:
    """Context manager that records every query executed while active.

    Usage:
        >>> with QueryTracker() as tracker:
        ...     pass  # code that may execute queries
        >>> tracker.violations(threshold=2)
        []
    """

    def __init__(self) -> None:
        self.events: list[QueryEvent] = []
        self._stack: ExitStack | None = None

    def __enter__(self) -> QueryTracker:
        self._stack = ExitStack()
        for connection in connections.all():
            self._stack.enter_context(connection.execute_wrapper(self._record))
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback_: TracebackType | None,
    ) -> None:
        if self._stack is not None:
            self._stack.close()
            self._stack = None

    def _record(
        self,
        execute: Any,
        sql: str,
        params: Any,
        many: bool,
        context: dict[str, Any],
    ) -> Any:
        result = execute(sql, params, many, context)
        connection = context.get("connection")
        alias = getattr(connection, "alias", "default")
        self.events.append(
            QueryEvent(
                sql=sql,
                fingerprint=normalize_sql(sql),
                alias=alias,
                call_site=_first_application_frame(),
            )
        )
        return result

    def violations(
        self, *, threshold: int, ignore_patterns: Sequence[re.Pattern[str]] = ()
    ) -> list[Violation]:
        """Group recorded events by fingerprint and report repeated ones.

        Args:
            threshold: The minimum number of occurrences of a fingerprint
                for it to be reported.
            ignore_patterns: Compiled regexes; a fingerprint matching any
                of them (via ``search``) is never reported, regardless of
                how many times it repeated.

        Returns:
            One :class:`Violation` per fingerprint that repeated at least
            ``threshold`` times, in first-seen order.
        """
        groups: dict[str, list[QueryEvent]] = {}
        order: list[str] = []
        for event in self.events:
            if any(pattern.search(event.fingerprint) for pattern in ignore_patterns):
                continue
            if event.fingerprint not in groups:
                groups[event.fingerprint] = []
                order.append(event.fingerprint)
            groups[event.fingerprint].append(event)

        violations: list[Violation] = []
        for fingerprint in order:
            events = groups[fingerprint]
            if len(events) < threshold:
                continue
            call_sites = tuple(dict.fromkeys(event.call_site for event in events))
            violations.append(
                Violation(
                    fingerprint=fingerprint,
                    count=len(events),
                    sample_sql=events[0].sql,
                    call_site=call_sites[0],
                    call_sites=call_sites,
                )
            )
        return violations


def _first_application_frame() -> str:
    for frame in reversed(traceback.extract_stack()):
        if not _is_library_frame(frame.filename):
            return f"{Path(frame.filename).name}:{frame.lineno}"
    return "<unknown>"


def _is_library_frame(filename: str) -> bool:
    normalized = filename.replace("\\", "/")
    if normalized.startswith(_OWN_PACKAGE_DIR):
        return True
    return any(marker in normalized for marker in _LIBRARY_MARKERS)
