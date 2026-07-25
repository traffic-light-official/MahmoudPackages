"""Management command: ``python manage.py generate_changelog``.

A convenience wrapper for projects that already run drf-spectacular:
generates the *current* project's OpenAPI schema and diffs it against
the schema committed at a previous Git ref, without needing to check
out that ref or run this project's standalone CLI separately.
"""

from __future__ import annotations

import tempfile
from argparse import ArgumentParser
from pathlib import Path
from typing import Any

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from drf_changelog_generator.changes import SchemaDiff
from drf_changelog_generator.diffing.engine import diff_schemas
from drf_changelog_generator.exceptions import ChangelogGeneratorError
from drf_changelog_generator.git_utils import load_schema_at_ref
from drf_changelog_generator.rendering.github import render_github_release_notes
from drf_changelog_generator.rendering.html import render_html
from drf_changelog_generator.rendering.markdown import render_markdown
from drf_changelog_generator.schema_loader import load_schema_file


class Command(BaseCommand):
    """Diff the current project's OpenAPI schema against a prior Git ref."""

    help = (
        "Diff the current project's OpenAPI schema (via drf-spectacular) "
        "against a previous Git ref."
    )

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Register this command's options."""
        parser.add_argument("--old-ref", required=True, help="Git ref to compare against.")
        parser.add_argument(
            "--schema-path",
            required=True,
            help="Path (relative to the repo root) the schema is committed at, at --old-ref.",
        )
        parser.add_argument(
            "--repo", default=".", help="Path to the Git repository (default: '.')."
        )
        parser.add_argument("--format", choices=["markdown", "html", "github"], default="markdown")
        parser.add_argument(
            "--repo-slug", default=None, help="'owner/name', for GitHub release note compare links."
        )
        parser.add_argument("--output", default=None, help="Write to this file instead of stdout.")
        parser.add_argument(
            "--fail-on-breaking",
            action="store_true",
            help="Exit with a non-zero status if breaking changes are found.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Generate the current schema, diff it, and render the result."""
        old_ref: str = options["old_ref"]
        schema_path: str = options["schema_path"]
        repo: str = options["repo"]

        try:
            old_schema = load_schema_at_ref(repo=repo, ref=old_ref, file_path=schema_path)
        except ChangelogGeneratorError as exc:
            raise CommandError(str(exc)) from exc

        with tempfile.TemporaryDirectory() as tmp_dir:
            current_schema_path = Path(tmp_dir) / "current-schema.yml"
            call_command("spectacular", file=str(current_schema_path))
            new_schema = load_schema_file(current_schema_path)

        diff = diff_schemas(old_schema, new_schema)
        rendered = self._render(
            diff, options["format"], old_ref, "working tree", options["repo_slug"]
        )

        output_path = options["output"]
        if output_path:
            Path(output_path).write_text(rendered, encoding="utf-8")
        else:
            self.stdout.write(rendered)

        if options["fail_on_breaking"] and diff.has_breaking_changes:
            raise CommandError("Breaking API changes detected.")

    def _render(
        self,
        diff: SchemaDiff,
        output_format: str,
        old_label: str,
        new_label: str,
        repo_slug: str | None,
    ) -> str:
        if output_format == "markdown":
            return render_markdown(diff, old_ref=old_label, new_ref=new_label)
        if output_format == "html":
            return render_html(diff, old_ref=old_label, new_ref=new_label)
        return render_github_release_notes(
            diff, old_ref=old_label, new_ref=new_label, repo=repo_slug
        )
