"""Compare two committed schema snapshots and print a text report.

Usage:
    python examples/compare_files.py openapi-baseline.yaml openapi-current.yaml
"""

from __future__ import annotations

import sys

from drf_contract_test import compare_schemas, load_schema_file
from drf_contract_test.reports import render_text


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(f"Usage: {argv[0]} <baseline> <current>", file=sys.stderr)
        return 2

    baseline = load_schema_file(argv[1])
    current = load_schema_file(argv[2])

    diff = compare_schemas(baseline, current)
    print(render_text(diff))

    return 1 if diff.has_breaking_changes else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
