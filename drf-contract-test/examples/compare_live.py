"""Compare a committed baseline against a live Django project's current schema.

Usage:
    DJANGO_SETTINGS_MODULE=myproject.settings python examples/compare_live.py openapi-baseline.yaml
"""

from __future__ import annotations

import sys

from drf_contract_test import compare_schemas, generate_schema, load_schema_file


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"Usage: {argv[0]} <baseline>", file=sys.stderr)
        return 2

    baseline = load_schema_file(argv[1])
    current = generate_schema()  # assumes DJANGO_SETTINGS_MODULE is already set

    diff = compare_schemas(baseline, current)
    for change in diff.changes:
        print(f"{change.severity.value.upper():8s} {change.operation} - {change.message}")

    return 1 if diff.has_breaking_changes else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
