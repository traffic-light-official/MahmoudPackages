"""Generate changelogs by diffing OpenAPI schemas between Git tags.

The public API is intentionally small. Most projects only need the
``drf-changelog-generator`` console script (see ``docs/quickstart.md``),
but the underlying pieces are all importable directly:

* :func:`~drf_changelog_generator.diffing.engine.diff_schemas` - the
  core diff engine, given two already-loaded schema dicts.
* :func:`~drf_changelog_generator.git_utils.load_schema_at_ref` - load a
  schema as it existed at a Git tag/branch/commit.
* :mod:`~drf_changelog_generator.rendering` - Markdown, HTML, Slack, and
  GitHub Release renderers.
"""

from __future__ import annotations

from drf_changelog_generator.changes import Change, ChangeKind, SchemaDiff, Severity
from drf_changelog_generator.diffing.engine import diff_schemas
from drf_changelog_generator.exceptions import ChangelogGeneratorError, GitError, SchemaParseError
from drf_changelog_generator.git_utils import load_schema_at_ref, show_file_at_ref
from drf_changelog_generator.rendering.github import render_github_release_notes
from drf_changelog_generator.rendering.html import render_html
from drf_changelog_generator.rendering.markdown import render_markdown
from drf_changelog_generator.rendering.slack import post_to_slack_webhook, render_slack_blocks
from drf_changelog_generator.schema_loader import load_schema_file, parse_schema

__version__ = "1.0.0"

__all__ = [
    "Change",
    "ChangeKind",
    "ChangelogGeneratorError",
    "GitError",
    "SchemaDiff",
    "SchemaParseError",
    "Severity",
    "__version__",
    "diff_schemas",
    "load_schema_at_ref",
    "load_schema_file",
    "parse_schema",
    "post_to_slack_webhook",
    "render_github_release_notes",
    "render_html",
    "render_markdown",
    "render_slack_blocks",
    "show_file_at_ref",
]
