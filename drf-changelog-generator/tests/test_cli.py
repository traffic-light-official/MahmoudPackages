"""Tests for :mod:`drf_changelog_generator.cli`."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from drf_changelog_generator.cli import main
from drf_changelog_generator.exceptions import ChangelogGeneratorError


@pytest.fixture
def schema_files(tmp_path: Path, old_schema: dict, new_schema: dict) -> tuple[Path, Path]:
    old_file = tmp_path / "old.yml"
    new_file = tmp_path / "new.yml"
    old_file.write_text(yaml.safe_dump(old_schema), encoding="utf-8")
    new_file.write_text(yaml.safe_dump(new_schema), encoding="utf-8")
    return old_file, new_file


class TestDiffWithLocalFiles:
    def test_prints_markdown_to_stdout_by_default(
        self, schema_files: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        old_file, new_file = schema_files

        exit_code = main(["diff", "--old-file", str(old_file), "--new-file", str(new_file)])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "# API Changelog" in captured.out

    def test_writes_to_output_file(self, schema_files: tuple[Path, Path], tmp_path: Path) -> None:
        old_file, new_file = schema_files
        output_file = tmp_path / "changelog.md"

        exit_code = main(
            [
                "diff",
                "--old-file",
                str(old_file),
                "--new-file",
                str(new_file),
                "--output",
                str(output_file),
            ]
        )

        assert exit_code == 0
        assert "# API Changelog" in output_file.read_text(encoding="utf-8")

    def test_html_format(
        self, schema_files: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        old_file, new_file = schema_files

        main(["diff", "--old-file", str(old_file), "--new-file", str(new_file), "--format", "html"])

        assert "<!doctype html>" in capsys.readouterr().out

    def test_slack_format_prints_valid_json(
        self, schema_files: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        old_file, new_file = schema_files

        main(
            ["diff", "--old-file", str(old_file), "--new-file", str(new_file), "--format", "slack"]
        )

        parsed = json.loads(capsys.readouterr().out)
        assert parsed[0]["type"] == "header"

    def test_github_format_with_repo_slug(
        self, schema_files: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        old_file, new_file = schema_files

        main(
            [
                "diff",
                "--old-file",
                str(old_file),
                "--new-file",
                str(new_file),
                "--format",
                "github",
                "--repo-slug",
                "myorg/myproject",
            ]
        )

        assert "myorg/myproject/compare" in capsys.readouterr().out

    def test_fail_on_breaking_exits_1_when_breaking_changes_found(
        self, schema_files: tuple[Path, Path]
    ) -> None:
        old_file, new_file = schema_files

        exit_code = main(
            [
                "diff",
                "--old-file",
                str(old_file),
                "--new-file",
                str(new_file),
                "--fail-on-breaking",
            ]
        )

        assert exit_code == 1

    def test_fail_on_breaking_exits_0_without_breaking_changes(
        self, tmp_path: Path, old_schema: dict
    ) -> None:
        old_file = tmp_path / "old.yml"
        new_file = tmp_path / "new.yml"
        old_file.write_text(yaml.safe_dump(old_schema), encoding="utf-8")
        new_file.write_text(yaml.safe_dump(old_schema), encoding="utf-8")

        exit_code = main(
            [
                "diff",
                "--old-file",
                str(old_file),
                "--new-file",
                str(new_file),
                "--fail-on-breaking",
            ]
        )

        assert exit_code == 0


class TestDiffWithGitRefs:
    def test_diffs_two_tags(self, git_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
        exit_code = main(
            [
                "diff",
                "--repo",
                str(git_repo),
                "--old-ref",
                "v1.0.0",
                "--new-ref",
                "v2.0.0",
                "--schema-path",
                "schema.yml",
            ]
        )

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "listComments" in captured.out or "/comments/" in captured.out


class TestErrorHandling:
    def test_missing_new_file_is_an_error(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        old_file = tmp_path / "old.yml"
        old_file.write_text("openapi: 3.0.3\n", encoding="utf-8")

        exit_code = main(["diff", "--old-file", str(old_file)])

        assert exit_code == 2
        assert "Error" in capsys.readouterr().err

    def test_repo_without_required_options_is_an_error(
        self, git_repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = main(["diff", "--repo", str(git_repo)])

        assert exit_code == 2
        assert "Error" in capsys.readouterr().err

    def test_unknown_git_ref_is_an_error(
        self, git_repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = main(
            [
                "diff",
                "--repo",
                str(git_repo),
                "--old-ref",
                "v1.0.0",
                "--new-ref",
                "does-not-exist",
                "--schema-path",
                "schema.yml",
            ]
        )

        assert exit_code == 2


class TestSlackWebhookPosting:
    def test_posts_to_webhook_when_requested(self, schema_files: tuple[Path, Path]) -> None:
        old_file, new_file = schema_files

        with patch("drf_changelog_generator.cli.post_to_slack_webhook") as mock_post:
            exit_code = main(
                [
                    "diff",
                    "--old-file",
                    str(old_file),
                    "--new-file",
                    str(new_file),
                    "--format",
                    "slack",
                    "--slack-webhook",
                    "https://hooks.slack.example/webhook",
                ]
            )

        assert exit_code == 0
        mock_post.assert_called_once()
        assert mock_post.call_args[0][0] == "https://hooks.slack.example/webhook"

    def test_webhook_failure_is_reported_and_exits_2(
        self, schema_files: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        old_file, new_file = schema_files

        with patch(
            "drf_changelog_generator.cli.post_to_slack_webhook",
            side_effect=ChangelogGeneratorError("boom"),
        ):
            exit_code = main(
                [
                    "diff",
                    "--old-file",
                    str(old_file),
                    "--new-file",
                    str(new_file),
                    "--format",
                    "slack",
                    "--slack-webhook",
                    "https://hooks.slack.example/webhook",
                ]
            )

        assert exit_code == 2
        assert "Error posting to Slack" in capsys.readouterr().err
