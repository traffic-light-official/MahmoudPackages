"""Shared change-partitioning logic used by every renderer.

Every renderer presents the same five, non-overlapping sections: added
endpoints, removed endpoints, deprecated endpoints, other breaking
changes, and other non-breaking changes. Partitioning this once here
keeps the four output formats consistent with each other.
"""

from __future__ import annotations

from dataclasses import dataclass

from drf_changelog_generator.changes import Change, ChangeKind, SchemaDiff, Severity

_ENDPOINT_KINDS = frozenset(
    {
        ChangeKind.ENDPOINT_ADDED,
        ChangeKind.ENDPOINT_REMOVED,
        ChangeKind.ENDPOINT_DEPRECATED,
        ChangeKind.ENDPOINT_UNDEPRECATED,
    }
)


@dataclass(frozen=True, slots=True)
class ChangeSummary:
    """A :class:`~drf_changelog_generator.changes.SchemaDiff`, partitioned for display."""

    added_endpoints: list[Change]
    removed_endpoints: list[Change]
    deprecated_endpoints: list[Change]
    other_breaking: list[Change]
    other_non_breaking: list[Change]

    @property
    def is_empty(self) -> bool:
        """Whether every section is empty."""
        return not (
            self.added_endpoints
            or self.removed_endpoints
            or self.deprecated_endpoints
            or self.other_breaking
            or self.other_non_breaking
        )


def summarize(diff: SchemaDiff) -> ChangeSummary:
    """Partition a diff's changes into the sections every renderer displays.

    Args:
        diff: The diff to partition.

    Returns:
        A :class:`ChangeSummary` with five non-overlapping lists.
    """
    added = [c for c in diff.changes if c.kind is ChangeKind.ENDPOINT_ADDED]
    removed = [c for c in diff.changes if c.kind is ChangeKind.ENDPOINT_REMOVED]
    deprecated = [
        c
        for c in diff.changes
        if c.kind in (ChangeKind.ENDPOINT_DEPRECATED, ChangeKind.ENDPOINT_UNDEPRECATED)
    ]
    other_breaking = [
        c for c in diff.changes if c.severity is Severity.BREAKING and c.kind not in _ENDPOINT_KINDS
    ]
    other_non_breaking = [
        c
        for c in diff.changes
        if c.severity is Severity.NON_BREAKING and c.kind not in _ENDPOINT_KINDS
    ]
    return ChangeSummary(
        added_endpoints=added,
        removed_endpoints=removed,
        deprecated_endpoints=deprecated,
        other_breaking=other_breaking,
        other_non_breaking=other_non_breaking,
    )
