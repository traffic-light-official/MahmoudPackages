"""The result of comparing two OpenAPI schemas: individual changes and their severity.

See ``docs/architecture.md`` for the reasoning behind why the same kind
of structural difference (a field becoming required, a value being added
to an enum, ...) is classified differently depending on whether it
occurred in a request or a response schema.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    """How a detected change affects API compatibility.

    Attributes:
        BREAKING: An existing, correctly-behaving client may now fail
            (a request it used to be able to send is rejected, or a
            response field it relied on is gone/changed shape).
        SAFE: The change only adds capability without removing any
            existing guarantee — no correctly-behaving existing client is
            affected.
        INFO: Neither breaking nor safe in a meaningful sense (e.g. a
            description-only change) — reported for completeness.
    """

    BREAKING = "breaking"
    SAFE = "safe"
    INFO = "info"


@dataclass(frozen=True, slots=True)
class Change:
    """A single detected difference between a baseline and current schema.

    Attributes:
        severity: How this change affects compatibility.
        operation: The affected operation, formatted as
            ``"<METHOD> <path>"`` (e.g. ``"POST /articles/"``), or
            ``None`` for schema-wide changes.
        location: Where within the operation this change occurred, e.g.
            ``"request.properties.category"`` or
            ``"responses.200.properties.title"``.
        kind: A short machine-readable identifier for the kind of change,
            e.g. ``"field_removed"``, ``"required_added"``,
            ``"type_changed"``, ``"enum_value_removed"``.
        message: A human-readable description of the change.
    """

    severity: Severity
    operation: str | None
    location: str
    kind: str
    message: str


@dataclass(frozen=True, slots=True)
class DiffResult:
    """The complete outcome of comparing a baseline schema to a current one.

    Attributes:
        changes: Every detected change, in the order they were found.
    """

    changes: tuple[Change, ...] = field(default_factory=tuple)

    @property
    def breaking_changes(self) -> tuple[Change, ...]:
        """Only the changes classified as :attr:`Severity.BREAKING`."""
        return tuple(c for c in self.changes if c.severity is Severity.BREAKING)

    @property
    def safe_changes(self) -> tuple[Change, ...]:
        """Only the changes classified as :attr:`Severity.SAFE`."""
        return tuple(c for c in self.changes if c.severity is Severity.SAFE)

    @property
    def info_changes(self) -> tuple[Change, ...]:
        """Only the changes classified as :attr:`Severity.INFO`."""
        return tuple(c for c in self.changes if c.severity is Severity.INFO)

    @property
    def has_breaking_changes(self) -> bool:
        """Whether any change is classified as :attr:`Severity.BREAKING`."""
        return any(c.severity is Severity.BREAKING for c in self.changes)
