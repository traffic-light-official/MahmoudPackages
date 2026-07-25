"""The ``drf-changelog-generator`` command-line interface.

Installed as a console script (see ``pyproject.toml``'s
``[project.scripts]``), so it works standalone in a GitHub Action or any
CI job without a Django project or ``manage.py`` in sight, as long as
the schema files being compared are available locally or in Git history.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from drf_changelog_generator.changes import SchemaDiff
from drf_changelog_generator.diffing.engine import diff_schemas
from drf_changelog_generator.exceptions import ChangelogGeneratorError
from drf_changelog_generator.git_utils import load_schema_at_ref
from drf_changelog_generator.rendering.github import render_github_release_notes
from drf_changelog_generator.rendering.html import render_html
from drf_changelog_generator.rendering.markdown import render_markdown
from drf_changelog_generator.rendering.slack import post_to_slack_webhook, render_slack_blocks
from drf_changelog_generator.schema_loader import load_schema_file

_FORMATS = ("markdown", "html", "slack", "github")


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="drf-changelog-generator",
        description="Generate a changelog by diffing two OpenAPI schema versions.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    diff_parser = subparsers.add_parser(
        "diff", help="Diff two OpenAPI schemas and render a changelog."
    )
    diff_parser.add_argument("--old-file", type=Path, help="Path to the earlier schema file.")
    diff_parser.add_argument("--new-file", type=Path, help="Path to the later schema file.")
    diff_parser.add_argument(
        "--repo", type=Path, help="Path to a Git repository to read schemas from, by ref."
    )
    diff_parser.add_argument("--old-ref", help="Git ref for the earlier schema (with --repo).")
    diff_parser.add_argument("--new-ref", help="Git ref for the later schema (with --repo).")
    diff_parser.add_argument(
        "--schema-path", help="Path to the schema file within the repo (with --repo)."
    )
    diff_parser.add_argument("--format", choices=_FORMATS, default="markdown")
    diff_parser.add_argument(
        "--output", type=Path, default=None, help="Write to this file instead of stdout."
    )
    diff_parser.add_argument(
        "--repo-slug", default=None, help="'owner/name', for GitHub release note compare links."
    )
    diff_parser.add_argument(
        "--slack-webhook", default=None, help="Post the rendered Slack blocks to this webhook URL."
    )
    diff_parser.add_argument(
        "--fail-on-breaking",
        action="store_true",
        help="Exit with status 1 if any breaking changes were detected.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI.

    Args:
        argv: Command-line arguments, excluding the program name.
            Defaults to ``sys.argv[1:]``.

    Returns:
        The process exit code: ``0`` on success, ``1`` if
        ``--fail-on-breaking`` was given and breaking changes were
        found, ``2`` on a usage/loading error.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        old_schema, new_schema, old_label, new_label = _load_schemas(args)
    except (ChangelogGeneratorError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    diff = diff_schemas(old_schema, new_schema)
    rendered = _render(diff, args.format, old_label, new_label, args.repo_slug)

    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")

    if args.format == "slack" and args.slack_webhook:
        blocks = render_slack_blocks(diff, old_ref=old_label, new_ref=new_label)
        try:
            post_to_slack_webhook(args.slack_webhook, blocks)
        except ChangelogGeneratorError as exc:
            print(f"Error posting to Slack: {exc}", file=sys.stderr)
            return 2

    if args.fail_on_breaking and diff.has_breaking_changes:
        return 1
    return 0


def _load_schemas(
    args: argparse.Namespace,
) -> tuple[dict[str, object], dict[str, object], str, str]:
    if args.repo is not None:
        if not (args.old_ref and args.new_ref and args.schema_path):
            raise ChangelogGeneratorError(
                "--repo requires --old-ref, --new-ref, and --schema-path."
            )
        old_schema = load_schema_at_ref(
            repo=args.repo, ref=args.old_ref, file_path=args.schema_path
        )
        new_schema = load_schema_at_ref(
            repo=args.repo, ref=args.new_ref, file_path=args.schema_path
        )
        return old_schema, new_schema, args.old_ref, args.new_ref

    if not args.old_file or not args.new_file:
        raise ChangelogGeneratorError(
            "Provide either --repo (with --old-ref/--new-ref/--schema-path) "
            "or both --old-file and --new-file."
        )
    old_schema = load_schema_file(args.old_file)
    new_schema = load_schema_file(args.new_file)
    return old_schema, new_schema, str(args.old_file), str(args.new_file)


def _render(
    diff: SchemaDiff, output_format: str, old_label: str, new_label: str, repo_slug: str | None
) -> str:
    if output_format == "markdown":
        return render_markdown(diff, old_ref=old_label, new_ref=new_label)
    if output_format == "html":
        return render_html(diff, old_ref=old_label, new_ref=new_label)
    if output_format == "slack":
        blocks = render_slack_blocks(diff, old_ref=old_label, new_ref=new_label)
        return json.dumps(blocks, indent=2) + "\n"
    if output_format == "github":
        return render_github_release_notes(
            diff, old_ref=old_label, new_ref=new_label, repo=repo_slug
        )
    raise ChangelogGeneratorError(f"Unknown output format: {output_format!r}")


if __name__ == "__main__":
    sys.exit(main())
