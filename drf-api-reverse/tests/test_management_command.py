"""Tests for the ``scaffold_api`` Django management command."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from django.core.management import CommandError, call_command


@pytest.fixture
def schema_file(sample_schema: dict[str, Any], tmp_path: Path) -> Path:
    path = tmp_path / "schema.yml"
    path.write_text(yaml.safe_dump(sample_schema), encoding="utf-8")
    return path


class TestScaffoldApiCommand:
    def test_generates_files(self, schema_file: Path, tmp_path: Path) -> None:
        output_dir = tmp_path / "app"
        call_command("scaffold_api", "--schema", str(schema_file), "--output", str(output_dir))
        assert (output_dir / "serializers.py").exists()

    def test_prints_created_message(
        self, schema_file: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        output_dir = tmp_path / "app"
        call_command("scaffold_api", "--schema", str(schema_file), "--output", str(output_dir))
        assert "Created" in capsys.readouterr().out

    def test_invalid_schema_raises_command_error(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.yml"
        bad.write_text(":\n  - not: [valid, {", encoding="utf-8")
        with pytest.raises(CommandError):
            call_command("scaffold_api", "--schema", str(bad), "--output", str(tmp_path / "app"))

    def test_missing_schema_file_raises_command_error(self, tmp_path: Path) -> None:
        with pytest.raises(CommandError):
            call_command(
                "scaffold_api",
                "--schema",
                str(tmp_path / "nope.yml"),
                "--output",
                str(tmp_path / "app"),
            )


class TestScaffoldApiCommandCheck:
    def test_check_passes_when_in_sync(self, schema_file: Path, tmp_path: Path) -> None:
        output_dir = tmp_path / "app"
        call_command("scaffold_api", "--schema", str(schema_file), "--output", str(output_dir))
        call_command(
            "scaffold_api", "--schema", str(schema_file), "--output", str(output_dir), "--check"
        )

    def test_check_raises_command_error_when_missing(
        self, schema_file: Path, tmp_path: Path
    ) -> None:
        output_dir = tmp_path / "app"
        with pytest.raises(CommandError):
            call_command(
                "scaffold_api",
                "--schema",
                str(schema_file),
                "--output",
                str(output_dir),
                "--check",
            )

    def test_check_prints_status_per_file(
        self, schema_file: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        output_dir = tmp_path / "app"
        call_command("scaffold_api", "--schema", str(schema_file), "--output", str(output_dir))
        capsys.readouterr()
        call_command(
            "scaffold_api", "--schema", str(schema_file), "--output", str(output_dir), "--check"
        )
        out = capsys.readouterr().out
        assert "serializers.py: in sync" in out
