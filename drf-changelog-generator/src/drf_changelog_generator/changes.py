"""The change data model produced by :mod:`drf_changelog_generator.diffing`."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    """Whether a detected change can break an existing API client."""

    #: An existing client following the OpenAPI contract may stop working.
    BREAKING = "breaking"
    #: An existing client is unaffected; only new capability was added.
    NON_BREAKING = "non_breaking"


class ChangeKind(str, Enum):
    """The specific kind of change detected between two schema versions."""

    ENDPOINT_ADDED = "endpoint_added"
    ENDPOINT_REMOVED = "endpoint_removed"
    ENDPOINT_DEPRECATED = "endpoint_deprecated"
    ENDPOINT_UNDEPRECATED = "endpoint_undeprecated"
    PARAMETER_ADDED = "parameter_added"
    PARAMETER_REMOVED = "parameter_removed"
    PARAMETER_REQUIRED_CHANGED = "parameter_required_changed"
    REQUEST_FIELD_ADDED = "request_field_added"
    REQUEST_FIELD_REMOVED = "request_field_removed"
    REQUEST_FIELD_REQUIRED_CHANGED = "request_field_required_changed"
    REQUEST_FIELD_TYPE_CHANGED = "request_field_type_changed"
    RESPONSE_ADDED = "response_added"
    RESPONSE_REMOVED = "response_removed"
    RESPONSE_FIELD_ADDED = "response_field_added"
    RESPONSE_FIELD_REMOVED = "response_field_removed"
    RESPONSE_FIELD_TYPE_CHANGED = "response_field_type_changed"


#: Change kinds concerning an operation's ``deprecated`` flag.
DEPRECATION_KINDS: frozenset[ChangeKind] = frozenset(
    {ChangeKind.ENDPOINT_DEPRECATED, ChangeKind.ENDPOINT_UNDEPRECATED}
)


@dataclass(frozen=True, slots=True)
class Change:
    """A single detected difference between two OpenAPI schema versions.

    Attributes:
        kind: The specific kind of change.
        severity: Whether this change can break an existing client.
        path: The OpenAPI path template, e.g. ``"/articles/{id}/"``.
        method: The HTTP method (lowercase), or ``None`` for a change
            that is not tied to one specific operation.
        location: A dotted pointer to where within the operation this
            change was found, e.g. ``"body.title"`` or
            ``"parameters.limit"``. Empty for endpoint-level changes.
        message: A human-readable description of the change.
    """

    kind: ChangeKind
    severity: Severity
    path: str
    method: str | None
    location: str
    message: str

    @property
    def operation_label(self) -> str:
        """A short ``"METHOD /path"`` (or just ``"/path"``) label for display."""
        if self.method is None:
            return self.path
        return f"{self.method.upper()} {self.path}"


@dataclass(frozen=True, slots=True)
class SchemaDiff:
    """The full set of changes detected between two OpenAPI schema versions."""

    changes: list[Change]

    @property
    def breaking_changes(self) -> list[Change]:
        """Every change with :attr:`Severity.BREAKING`."""
        return [change for change in self.changes if change.severity is Severity.BREAKING]

    @property
    def non_breaking_changes(self) -> list[Change]:
        """Every change with :attr:`Severity.NON_BREAKING`."""
        return [change for change in self.changes if change.severity is Severity.NON_BREAKING]

    @property
    def has_breaking_changes(self) -> bool:
        """Whether any detected change is breaking."""
        return any(change.severity is Severity.BREAKING for change in self.changes)

    @property
    def is_empty(self) -> bool:
        """Whether no changes were detected at all."""
        return not self.changes
