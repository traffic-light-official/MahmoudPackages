"""Tests for the ``generate_changelog`` management command."""

from __future__ import annotations

from io import StringIO
from pathlib import Path

import pytest
from django.core.management import CommandError, call_command

pytestmark = pytest.mark.django_db


class TestGenerateChangelogCommand:
    def test_diffs_current_schema_against_a_git_ref(self, git_repo: Path) -> None:
        out = StringIO()

        call_command(
            "generate_changelog",
            old_ref="v1.0.0",
            schema_path="schema.yml",
            repo=str(git_repo),
            stdout=out,
        )

        rendered = out.getvalue()
        assert "# API Changelog" in rendered
        assert "working tree" in rendered

    def test_writes_to_output_file(self, git_repo: Path, tmp_path: Path) -> None:
        output_file = tmp_path / "changelog.md"

        call_command(
            "generate_changelog",
            old_ref="v1.0.0",
            schema_path="schema.yml",
            repo=str(git_repo),
            output=str(output_file),
        )

        assert "# API Changelog" in output_file.read_text(encoding="utf-8")

    def test_github_format(self, git_repo: Path) -> None:
        out = StringIO()

        call_command(
            "generate_changelog",
            old_ref="v1.0.0",
            schema_path="schema.yml",
            repo=str(git_repo),
            format="github",
            repo_slug="myorg/myproject",
            stdout=out,
        )

        assert "myorg/myproject/compare" in out.getvalue()

    def test_unknown_ref_raises_command_error(self, git_repo: Path) -> None:
        with pytest.raises(CommandError):
            call_command(
                "generate_changelog",
                old_ref="does-not-exist",
                schema_path="schema.yml",
                repo=str(git_repo),
            )

    def test_fail_on_breaking_raises_when_breaking_changes_found(self, git_repo: Path) -> None:
        # v2.0.0's schema.yml includes a "/comments/" path the test project's
        # real ArticleViewSet-based schema does not have, so comparing
        # against it always yields at least one removed (breaking) endpoint.
        with pytest.raises(CommandError, match="Breaking API changes"):
            call_command(
                "generate_changelog",
                old_ref="v2.0.0",
                schema_path="schema.yml",
                repo=str(git_repo),
                fail_on_breaking=True,
            )
