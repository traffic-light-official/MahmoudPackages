"""Tests for :mod:`drf_changelog_generator.rendering.github`."""

from __future__ import annotations

from drf_changelog_generator.changes import SchemaDiff
from drf_changelog_generator.diffing.engine import diff_schemas
from drf_changelog_generator.rendering.github import render_github_release_notes


class TestRenderGithubReleaseNotes:
    def test_empty_diff(self) -> None:
        rendered = render_github_release_notes(
            SchemaDiff(changes=[]), old_ref="v1.0.0", new_ref="v1.1.0"
        )

        assert "No API changes in this release." in rendered

    def test_includes_a_compare_link_when_repo_given(self) -> None:
        rendered = render_github_release_notes(
            SchemaDiff(changes=[]),
            old_ref="v1.0.0",
            new_ref="v1.1.0",
            repo="myorg/myproject",
        )

        assert "https://github.com/myorg/myproject/compare/v1.0.0...v1.1.0" in rendered

    def test_omits_compare_link_without_repo(self) -> None:
        rendered = render_github_release_notes(
            SchemaDiff(changes=[]), old_ref="v1.0.0", new_ref="v1.1.0"
        )

        assert "compare" not in rendered

    def test_rich_diff_produces_expected_sections(self, old_schema: dict, new_schema: dict) -> None:
        diff = diff_schemas(old_schema, new_schema)

        rendered = render_github_release_notes(diff, old_ref="v1.0.0", new_ref="v1.1.0")

        assert "## :warning: Breaking API Changes" in rendered
        assert "## Deprecated" in rendered
        assert "## Added" in rendered
        assert "## Other API Changes" in rendered
        assert "`DELETE /articles/{id}/`" in rendered

    def test_ends_with_a_trailing_newline(self) -> None:
        rendered = render_github_release_notes(SchemaDiff(changes=[]), old_ref="a", new_ref="b")

        assert rendered.endswith("\n")
        assert not rendered.endswith("\n\n")
