"""The ``drf-api-reverse`` command-line interface.

Installed as a console script (see ``pyproject.toml``'s
``[project.scripts]``), so it works standalone in a GitHub Action or any
CI job without a Django project or ``manage.py`` in sight.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from drf_api_reverse.checker import check_drift
from drf_api_reverse.exceptions import ApiReverseError
from drf_api_reverse.scaffolder import scaffold
from drf_api_reverse.schema_loader import load_schema_file


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="drf-api-reverse",
        description="Scaffold DRF serializers/viewsets/urls from an OpenAPI contract.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    scaffold_parser = subparsers.add_parser(
        "scaffold", help="Generate or idempotently regenerate serializers.py/views.py/urls.py."
    )
    scaffold_parser.add_argument(
        "--schema", required=True, type=Path, help="Path to the OpenAPI schema."
    )
    scaffold_parser.add_argument(
        "--output", required=True, type=Path, help="Directory to write the generated files into."
    )

    check_parser = subparsers.add_parser(
        "check", help="Fail if generated code has drifted from the current schema."
    )
    check_parser.add_argument(
        "--schema", required=True, type=Path, help="Path to the OpenAPI schema."
    )
    check_parser.add_argument(
        "--output", required=True, type=Path, help="Directory previously scaffolded into."
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI.

    Args:
        argv: Command-line arguments, excluding the program name.
            Defaults to ``sys.argv[1:]``.

    Returns:
        The process exit code: ``0`` on success, ``1`` if ``check``
        found drift, ``2`` on a usage/loading error.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        schema = load_schema_file(args.schema)
    except (ApiReverseError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if args.command == "scaffold":
        results = scaffold(schema, args.output)
        for result in results:
            verb = "Created" if result.created else "Updated"
            print(f"{verb} {args.output / result.filename}")
            for key in result.orphaned_keys:
                print(f"  note: region {key!r} has no corresponding schema entry, left as-is")
        return 0

    reports = check_drift(schema, args.output)
    drifted = [report for report in reports if report.has_drift]
    for report in reports:
        status = "DRIFTED" if report.has_drift else "in sync"
        print(f"{report.filename}: {status}")
        if report.file_missing:
            print("  file does not exist - run `drf-api-reverse scaffold` first")
            continue
        for key in report.changed_keys:
            print(f"  changed: {key}")
        for key in report.missing_keys:
            print(f"  missing (schema has it, file doesn't): {key}")
        for key in report.orphaned_keys:
            print(f"  orphaned (file has it, schema doesn't): {key}")

    return 1 if drifted else 0


if __name__ == "__main__":
    sys.exit(main())
