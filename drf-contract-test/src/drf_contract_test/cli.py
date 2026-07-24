"""The ``drf-contract-test`` command-line tool.

Three subcommands:

- ``snapshot``: generate a schema from a live Django project and write it
  to a file — typically committed as your baseline.
- ``compare``: compare two schema files (or a file against a freshly
  generated live schema) and print a report; exits non-zero if breaking
  changes are found.
- ``check``: like ``compare``, but also enforces that breaking changes
  are accompanied by a version bump (see
  :func:`drf_contract_test.versioning.check_version_bump`); intended for
  CI.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from drf_contract_test.changes import DiffResult
from drf_contract_test.diff import compare_schemas
from drf_contract_test.exceptions import ContractTestError
from drf_contract_test.reports import render_html, render_json, render_text
from drf_contract_test.schema import Schema, dump_schema_file, generate_schema, load_schema_file
from drf_contract_test.versioning import VersionCheckResult, check_version_bump


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the ``drf-contract-test`` console script.

    Args:
        argv: Command-line arguments, excluding the program name. Defaults
            to :data:`sys.argv[1:]`.

    Returns:
        The process exit code (``0`` for success).
    """
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except ContractTestError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="drf-contract-test", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    snapshot_parser = subparsers.add_parser(
        "snapshot", help="Generate a schema snapshot from a live Django project."
    )
    snapshot_parser.add_argument(
        "output", help="Path to write the schema to (.json or .yaml/.yml)."
    )
    snapshot_parser.add_argument(
        "--settings", help="Dotted path to the Django settings module.", default=None
    )
    snapshot_parser.add_argument(
        "--urlconf", help="Dotted path to the URLconf module.", default=None
    )
    snapshot_parser.set_defaults(handler=_handle_snapshot)

    compare_parser = subparsers.add_parser(
        "compare", help="Compare two schemas and report changes."
    )
    _add_compare_arguments(compare_parser)
    compare_parser.set_defaults(handler=_handle_compare)

    check_parser = subparsers.add_parser(
        "check",
        help="Compare two schemas and additionally enforce a version bump for breaking changes.",
    )
    _add_compare_arguments(check_parser)
    check_parser.add_argument(
        "--require-major-bump",
        action="store_true",
        help="Require the major version component specifically to increase (not just any change).",
    )
    check_parser.set_defaults(handler=_handle_check)

    return parser


def _add_compare_arguments(subparser: argparse.ArgumentParser) -> None:
    subparser.add_argument("baseline", help="Path to the baseline schema file.")
    subparser.add_argument(
        "current",
        nargs="?",
        default=None,
        help="Path to the current schema file. If omitted, generated live via settings/urlconf.",
    )
    subparser.add_argument(
        "--settings", help="Dotted path to the Django settings module.", default=None
    )
    subparser.add_argument("--urlconf", help="Dotted path to the URLconf module.", default=None)
    subparser.add_argument(
        "--format", choices=["text", "json", "html"], default="text", help="Report format."
    )
    subparser.add_argument(
        "--output", help="Write the report to this path instead of stdout.", default=None
    )
    subparser.add_argument(
        "--no-fail-on-breaking",
        dest="fail_on_breaking",
        action="store_false",
        default=True,
        help="Exit 0 even if breaking changes are detected (default: exit non-zero).",
    )


def _handle_snapshot(args: argparse.Namespace) -> int:
    schema = generate_schema(settings_module=args.settings, urlconf=args.urlconf)
    dump_schema_file(schema, args.output)
    print(f"Wrote schema snapshot to {args.output}")
    return 0


def _load_current(args: argparse.Namespace) -> Schema:
    if args.current:
        return load_schema_file(args.current)
    return generate_schema(settings_module=args.settings, urlconf=args.urlconf)


def _handle_compare(args: argparse.Namespace) -> int:
    baseline = load_schema_file(args.baseline)
    current = _load_current(args)
    diff = compare_schemas(baseline, current)
    _emit_report(args, diff)
    return 1 if (args.fail_on_breaking and diff.has_breaking_changes) else 0


def _handle_check(args: argparse.Namespace) -> int:
    baseline = load_schema_file(args.baseline)
    current = _load_current(args)
    diff = compare_schemas(baseline, current)
    version_check = check_version_bump(
        baseline, current, diff, require_major_bump=args.require_major_bump
    )
    _emit_report(args, diff, version_check=version_check)
    if not args.fail_on_breaking:
        return 0
    return 0 if version_check.ok else 1


def _emit_report(
    args: argparse.Namespace, diff: DiffResult, *, version_check: VersionCheckResult | None = None
) -> None:
    renderers = {"text": render_text, "json": render_json, "html": render_html}
    report = renderers[args.format](diff, version_check=version_check)
    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"Wrote {args.format} report to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    sys.exit(main())
