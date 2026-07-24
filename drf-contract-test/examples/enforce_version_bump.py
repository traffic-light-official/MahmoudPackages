"""Fail unless a version bump accompanies any breaking API change.

Usage:
    python examples/enforce_version_bump.py openapi-baseline.yaml --settings myproject.settings
"""

from __future__ import annotations

import argparse
import sys

from drf_contract_test import check_version_bump, compare_schemas, generate_schema, load_schema_file


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline")
    parser.add_argument("--settings", default=None)
    parser.add_argument("--require-major-bump", action="store_true")
    args = parser.parse_args(argv)

    baseline = load_schema_file(args.baseline)
    current = generate_schema(settings_module=args.settings)
    diff = compare_schemas(baseline, current)

    result = check_version_bump(baseline, current, diff, require_major_bump=args.require_major_bump)
    print(result.message)
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
