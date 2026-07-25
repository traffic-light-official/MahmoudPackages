"""Detects drift between the OpenAPI contract and previously scaffolded code.

"Drift" here means: the generated regions on disk no longer match what
``scaffold`` would produce *right now* from the schema - either because
the schema changed since the last ``scaffold`` run, or because someone
hand-edited text inside a generated region (which
:mod:`drf_api_reverse.regions` always overwrites on the next real run,
so a mismatch here is a signal to re-run ``scaffold`` deliberately, not
evidence of a bug).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from drf_api_reverse.exceptions import DriftDetectedError
from drf_api_reverse.regions import parse_regions
from drf_api_reverse.scaffolder import GENERATORS


@dataclass(frozen=True, slots=True)
class FileDrift:
    """Drift found in a single generated file."""

    filename: str
    file_missing: bool = False
    changed_keys: list[str] = field(default_factory=list)
    """Regions present on disk whose content no longer matches the schema."""
    missing_keys: list[str] = field(default_factory=list)
    """Regions the schema now expects that are absent from the file."""
    orphaned_keys: list[str] = field(default_factory=list)
    """Regions on disk with no corresponding entry in the current schema."""

    @property
    def has_drift(self) -> bool:
        """Whether this file differs from what the schema currently implies."""
        return bool(
            self.file_missing or self.changed_keys or self.missing_keys or self.orphaned_keys
        )


def check_drift(schema: dict[str, Any], output_dir: str | Path) -> list[FileDrift]:
    """Compare on-disk generated regions against the current schema.

    Args:
        schema: The full parsed OpenAPI document.
        output_dir: The Django app directory ``scaffold`` was previously
            run against.

    Returns:
        One :class:`FileDrift` per file this package generates, always
        in ``serializers.py``, ``views.py``, ``urls.py`` order,
        regardless of whether drift was found.
    """
    output_dir = Path(output_dir)
    reports: list[FileDrift] = []

    for filename, generate_regions, _render_file in GENERATORS:
        target = output_dir / filename
        expected = generate_regions(schema)

        if not target.exists():
            reports.append(
                FileDrift(filename=filename, file_missing=True, missing_keys=list(expected))
            )
            continue

        existing_chunks = {
            chunk.key: chunk.text
            for chunk in parse_regions(target.read_text(encoding="utf-8"))
            if chunk.is_region and chunk.key is not None
        }

        changed = [
            key
            for key, body in expected.items()
            if key in existing_chunks and existing_chunks[key] != body
        ]
        missing = [key for key in expected if key not in existing_chunks]
        orphaned = [key for key in existing_chunks if key not in expected]

        reports.append(
            FileDrift(
                filename=filename,
                changed_keys=changed,
                missing_keys=missing,
                orphaned_keys=orphaned,
            )
        )

    return reports


def raise_if_drifted(schema: dict[str, Any], output_dir: str | Path) -> list[FileDrift]:
    """Like :func:`check_drift`, but raises if any file has drifted.

    Raises:
        DriftDetectedError: If any returned :class:`FileDrift` has
            ``has_drift`` set.
    """
    reports = check_drift(schema, output_dir)
    drifted = [report for report in reports if report.has_drift]
    if drifted:
        names = ", ".join(report.filename for report in drifted)
        raise DriftDetectedError(f"Generated code has drifted from the schema in: {names}.")
    return reports
