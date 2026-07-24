"""Enforcing an API version bump alongside breaking changes.

The whole point of detecting breaking changes is to make sure they're
*communicated* — typically via a version bump clients can key off of.
:func:`check_version_bump` fails when breaking changes exist but the
``info.version`` field didn't change (or, optionally, didn't change at
the major-version component specifically).
"""

from __future__ import annotations

from dataclasses import dataclass

from drf_contract_test.changes import DiffResult
from drf_contract_test.schema import Schema


@dataclass(frozen=True, slots=True)
class VersionCheckResult:
    """The outcome of checking whether a version bump matches breaking changes.

    Attributes:
        ok: Whether the version bump (or lack of breaking changes)
            satisfies the requirement.
        message: A human-readable explanation.
        baseline_version: The baseline schema's ``info.version``.
        current_version: The current schema's ``info.version``.
    """

    ok: bool
    message: str
    baseline_version: str
    current_version: str


def check_version_bump(
    baseline: Schema, current: Schema, diff: DiffResult, *, require_major_bump: bool = False
) -> VersionCheckResult:
    """Check that breaking changes are accompanied by a version bump.

    Args:
        baseline: The previous schema.
        current: The new schema.
        diff: The result of comparing them (see
            :func:`drf_contract_test.diff.compare_schemas`).
        require_major_bump: If ``True``, the *major* version component
            specifically must increase (not just any change to the
            version string). Requires both versions to start with a
            parseable integer component (an optional leading ``v`` is
            tolerated); if either doesn't, this check is skipped with a
            note in the message rather than raising, since not every
            project uses semver.

    Returns:
        A :class:`VersionCheckResult`.
    """
    baseline_version = baseline.version
    current_version = current.version

    if not diff.has_breaking_changes:
        return VersionCheckResult(
            ok=True,
            message="No breaking changes detected; no version bump required.",
            baseline_version=baseline_version,
            current_version=current_version,
        )

    if require_major_bump:
        old_major = _parse_major(baseline_version)
        new_major = _parse_major(current_version)
        if old_major is None or new_major is None:
            return VersionCheckResult(
                ok=baseline_version != current_version,
                message=(
                    f"{len(diff.breaking_changes)} breaking change(s) detected. Could not parse "
                    f"a major version component from {baseline_version!r}/{current_version!r} to "
                    f"enforce a major bump specifically; falling back to checking that the "
                    f"version string changed at all."
                ),
                baseline_version=baseline_version,
                current_version=current_version,
            )
        ok = new_major > old_major
        message = (
            f"{len(diff.breaking_changes)} breaking change(s) detected and the major version "
            f"was bumped ({baseline_version!r} -> {current_version!r})."
            if ok
            else (
                f"{len(diff.breaking_changes)} breaking change(s) detected but the major version "
                f"was not bumped (still major version {new_major}, in {current_version!r})."
            )
        )
        return VersionCheckResult(ok, message, baseline_version, current_version)

    ok = baseline_version != current_version
    message = (
        f"{len(diff.breaking_changes)} breaking change(s) detected and the API version was "
        f"bumped ({baseline_version!r} -> {current_version!r})."
        if ok
        else (
            f"{len(diff.breaking_changes)} breaking change(s) detected but the API version was "
            f"not bumped (still {current_version!r})."
        )
    )
    return VersionCheckResult(ok, message, baseline_version, current_version)


def _parse_major(version: str) -> int | None:
    if not version:
        return None
    first_segment = version.split(".", maxsplit=1)[0].strip().lower()
    if first_segment.startswith("v"):
        first_segment = first_segment[1:]
    return int(first_segment) if first_segment.isdigit() else None
