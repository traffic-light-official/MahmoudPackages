"""The recorded profile data shape, and the measurement primitive that fills it.

Query counting uses Django's public ``connection.execute_wrapper()``
hook (stable since Django 3.0) across every configured database alias
(via ``connections.all()``) - the same instrumentation technique used
by this workspace's ``drf-n-plus-one-query-guard`` package - rather
than monkeypatching the ORM.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from django.db import connections

if TYPE_CHECKING:
    from rest_framework.serializers import BaseSerializer


@dataclass
class FieldProfile:
    """Aggregated timing/query stats for one field, across every row profiled.

    Attributes:
        field_name: The field's name on the serializer.
        total_time_ms: Total time spent in this field's
            ``get_attribute()`` + ``to_representation()``, summed
            across every row.
        call_count: How many rows this field was actually rendered for
            (a field skipped via ``SkipField`` for a given row is not
            counted).
        query_count: Total number of database queries triggered while
            rendering this field, summed across every row.
    """

    field_name: str
    total_time_ms: float = 0.0
    call_count: int = 0
    query_count: int = 0

    def record(self, elapsed_ms: float, query_count: int) -> None:
        """Add one more row's measurement into this field's running totals."""
        self.total_time_ms += elapsed_ms
        self.call_count += 1
        self.query_count += query_count

    @property
    def average_time_ms(self) -> float:
        """Average per-row time, or ``0.0`` if this field was never rendered."""
        return self.total_time_ms / self.call_count if self.call_count else 0.0

    def as_dict(self) -> dict[str, Any]:
        """Render as a plain, JSON-serializable dict."""
        return {
            "field_name": self.field_name,
            "total_time_ms": round(self.total_time_ms, 3),
            "average_time_ms": round(self.average_time_ms, 3),
            "call_count": self.call_count,
            "query_count": self.query_count,
        }


@dataclass
class SerializerProfile:
    """Every field's :class:`FieldProfile`, keyed by field name."""

    fields: dict[str, FieldProfile] = field(default_factory=dict)

    def record(self, field_name: str, elapsed_ms: float, query_count: int) -> None:
        """Record one row's measurement for ``field_name``, creating it if new."""
        self.fields.setdefault(field_name, FieldProfile(field_name)).record(elapsed_ms, query_count)

    @property
    def total_time_ms(self) -> float:
        """Sum of every field's ``total_time_ms``."""
        return sum(profile.total_time_ms for profile in self.fields.values())

    @property
    def total_query_count(self) -> int:
        """Sum of every field's ``query_count``."""
        return sum(profile.query_count for profile in self.fields.values())

    def slowest_fields(self, limit: int | None = None) -> list[FieldProfile]:
        """Return every field's profile, slowest (`total_time_ms`) first."""
        ordered = sorted(
            self.fields.values(), key=lambda profile: profile.total_time_ms, reverse=True
        )
        return ordered[:limit] if limit is not None else ordered

    def as_dict(self) -> dict[str, Any]:
        """Render as a plain, JSON-serializable dict."""
        return {
            "fields": [profile.as_dict() for profile in self.slowest_fields()],
            "total_time_ms": round(self.total_time_ms, 3),
            "total_query_count": self.total_query_count,
        }

    def as_header_value(self, max_fields: int = 5) -> str:
        """Render the slowest ``max_fields`` fields as a compact, single-line summary."""
        parts = [
            f"{profile.field_name}={profile.total_time_ms:.2f}ms ({profile.query_count}q)"
            for profile in self.slowest_fields(max_fields)
        ]
        summary = ", ".join(parts)
        return f"{summary} (total={self.total_time_ms:.2f}ms, queries={self.total_query_count})"


def merge_profiles(profiles: list[SerializerProfile]) -> SerializerProfile:
    """Combine several profiles (e.g. one per serializer captured during a request) into one."""
    merged = SerializerProfile()
    for profile in profiles:
        for field_profile in profile.fields.values():
            merged.record(
                field_profile.field_name, field_profile.total_time_ms, field_profile.query_count
            )
    return merged


def get_serializer_profile(serializer: BaseSerializer[Any] | None) -> SerializerProfile | None:
    """Return the :class:`SerializerProfile` recorded on ``serializer``.

    Returns ``None`` if ``serializer`` is ``None``, doesn't mix in
    :class:`~drf_serializer_performance_profiler.mixins.ProfileSerializerMixin`,
    or instrumentation never ran (both ``ENABLED`` and
    ``LOG_SLOW_FIELDS`` were ``False`` for every field rendered).
    """
    return getattr(serializer, "_serializer_profile", None)


@dataclass
class _Measurement:
    elapsed_ms: float = 0.0
    query_count: int = 0


@contextmanager
def measure() -> Iterator[_Measurement]:
    """Time a block of code and count every database query it triggers.

    Wraps every currently configured database connection's
    ``execute_wrapper()`` for the duration of the block - covers
    whichever alias(es) the wrapped code actually queries, without
    needing to know in advance which one that is.
    """
    measurement = _Measurement()
    query_count = 0

    def wrapper(execute: Any, sql: Any, params: Any, many: Any, context: Any) -> Any:
        nonlocal query_count
        query_count += 1
        return execute(sql, params, many, context)

    start = time.perf_counter()
    with ExitStack() as stack:
        for connection in connections.all():
            stack.enter_context(connection.execute_wrapper(wrapper))
        try:
            yield measurement
        finally:
            measurement.elapsed_ms = (time.perf_counter() - start) * 1000
            measurement.query_count = query_count
