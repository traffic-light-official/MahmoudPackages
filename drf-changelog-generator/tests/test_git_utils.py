"""Tests for :mod:`drf_changelog_generator.git_utils`."""

from __future__ import annotations

from pathlib import Path

import pytest

from drf_changelog_generator.exceptions import GitError
from drf_changelog_generator.git_utils import load_schema_at_ref, show_file_at_ref


class TestShowFileAtRef:
    def test_reads_file_content_at_a_tag(self, git_repo: Path) -> None:
        content = show_file_at_ref(repo=git_repo, ref="v1.0.0", file_path="schema.yml")

        assert "listArticles" in content
        assert "listComments" not in content

    def test_reads_a_later_version_at_a_different_tag(self, git_repo: Path) -> None:
        content = show_file_at_ref(repo=git_repo, ref="v2.0.0", file_path="schema.yml")

        assert "listComments" in content

    def test_raises_for_an_unknown_ref(self, git_repo: Path) -> None:
        with pytest.raises(GitError):
            show_file_at_ref(repo=git_repo, ref="v99.0.0", file_path="schema.yml")

    def test_raises_for_a_missing_file(self, git_repo: Path) -> None:
        with pytest.raises(GitError):
            show_file_at_ref(repo=git_repo, ref="v1.0.0", file_path="does-not-exist.yml")

    def test_raises_for_a_non_git_directory(self, tmp_path: Path) -> None:
        not_a_repo = tmp_path / "not-a-repo"
        not_a_repo.mkdir()

        with pytest.raises(GitError):
            show_file_at_ref(repo=not_a_repo, ref="v1.0.0", file_path="schema.yml")


class TestLoadSchemaAtRef:
    def test_loads_and_parses_the_schema(self, git_repo: Path) -> None:
        schema = load_schema_at_ref(repo=git_repo, ref="v1.0.0", file_path="schema.yml")

        assert "/articles/" in schema["paths"]
        assert "/comments/" not in schema["paths"]
