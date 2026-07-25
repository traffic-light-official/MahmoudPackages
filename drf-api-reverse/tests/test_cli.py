"""Tests for :mod:`drf_api_reverse.cli`."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from drf_api_reverse.cli import main


@pytest.fixture
def schema_file(sample_schema: dict[str, Any], tmp_path: Path) -> Path:
    path = tmp_path / "schema.yml"
    path.write_text(yaml.safe_dump(sample_schema), encoding="utf-8")
    return path


class TestScaffoldCommand:
    def test_exit_code_zero_on_success(self, schema_file: Path, tmp_path: Path) -> None:
        output_dir = tmp_path / "app"
        exit_code = main(["scaffold", "--schema", str(schema_file), "--output", str(output_dir)])
        assert exit_code == 0
        assert (output_dir / "serializers.py").exists()

    def test_prints_created_for_each_file(
        self, schema_file: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        output_dir = tmp_path / "app"
        main(["scaffold", "--schema", str(schema_file), "--output", str(output_dir)])
        out = capsys.readouterr().out
        assert "Created" in out
        assert "serializers.py" in out
        assert "views.py" in out
        assert "urls.py" in out

    def test_second_run_prints_updated(
        self, schema_file: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        output_dir = tmp_path / "app"
        main(["scaffold", "--schema", str(schema_file), "--output", str(output_dir)])
        capsys.readouterr()
        main(["scaffold", "--schema", str(schema_file), "--output", str(output_dir)])
        assert "Updated" in capsys.readouterr().out

    def test_orphaned_region_prints_a_note(
        self,
        sample_schema: dict[str, Any],
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        full_file = tmp_path / "full.yml"
        full_file.write_text(yaml.safe_dump(sample_schema), encoding="utf-8")
        output_dir = tmp_path / "app"
        main(["scaffold", "--schema", str(full_file), "--output", str(output_dir)])
        capsys.readouterr()

        shrunk_schema = {
            "components": {
                "schemas": {
                    k: v
                    for k, v in sample_schema["components"]["schemas"].items()
                    if k != "Comment"
                }
            },
            "paths": sample_schema["paths"],
        }
        shrunk_file = tmp_path / "shrunk.yml"
        shrunk_file.write_text(yaml.safe_dump(shrunk_schema), encoding="utf-8")

        main(["scaffold", "--schema", str(shrunk_file), "--output", str(output_dir)])
        out = capsys.readouterr().out
        assert "note: region 'serializer:Comment' has no corresponding schema entry" in out


class TestCheckCommand:
    def test_exit_code_zero_when_in_sync(self, schema_file: Path, tmp_path: Path) -> None:
        output_dir = tmp_path / "app"
        main(["scaffold", "--schema", str(schema_file), "--output", str(output_dir)])
        exit_code = main(["check", "--schema", str(schema_file), "--output", str(output_dir)])
        assert exit_code == 0

    def test_exit_code_one_when_missing(self, schema_file: Path, tmp_path: Path) -> None:
        output_dir = tmp_path / "app"
        exit_code = main(["check", "--schema", str(schema_file), "--output", str(output_dir)])
        assert exit_code == 1

    def test_prints_drift_status_per_file(
        self, schema_file: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        output_dir = tmp_path / "app"
        main(["check", "--schema", str(schema_file), "--output", str(output_dir)])
        out = capsys.readouterr().out
        assert "serializers.py: DRIFTED" in out
        assert "file does not exist" in out

    def test_prints_changed_missing_and_orphaned_keys(
        self,
        sample_schema: dict[str, Any],
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        full_file = tmp_path / "full.yml"
        full_file.write_text(yaml.safe_dump(sample_schema), encoding="utf-8")
        output_dir = tmp_path / "app"
        main(["scaffold", "--schema", str(full_file), "--output", str(output_dir)])
        capsys.readouterr()

        schemas = dict(sample_schema["components"]["schemas"])
        schemas.pop("Comment")
        schemas["Author"] = {
            "type": "object",
            "properties": {"nickname": {"type": "string"}},
        }
        schemas["NewOne"] = {"type": "object", "properties": {"x": {"type": "string"}}}
        modified_schema = {
            "components": {"schemas": schemas},
            "paths": sample_schema["paths"],
        }
        modified_file = tmp_path / "modified.yml"
        modified_file.write_text(yaml.safe_dump(modified_schema), encoding="utf-8")

        exit_code = main(["check", "--schema", str(modified_file), "--output", str(output_dir)])
        out = capsys.readouterr().out

        assert exit_code == 1
        assert "changed: serializer:Author" in out
        assert "missing (schema has it, file doesn't): serializer:NewOne" in out
        assert "orphaned (file has it, schema doesn't): serializer:Comment" in out


class TestCliErrors:
    def test_missing_schema_file_exits_2(self, tmp_path: Path) -> None:
        exit_code = main(
            ["scaffold", "--schema", str(tmp_path / "nope.yml"), "--output", str(tmp_path / "app")]
        )
        assert exit_code == 2

    def test_unparsable_schema_exits_2(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        bad = tmp_path / "bad.yml"
        bad.write_text(":\n  - not: [valid, {", encoding="utf-8")
        exit_code = main(["scaffold", "--schema", str(bad), "--output", str(tmp_path / "app")])
        assert exit_code == 2
        assert "Error:" in capsys.readouterr().err

    def test_missing_required_argument_raises_systemexit(self) -> None:
        with pytest.raises(SystemExit):
            main(["scaffold", "--schema", "x.yml"])
