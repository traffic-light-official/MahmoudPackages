"""Tests for the drf-contract-test CLI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from drf_contract_test.cli import main
from drf_contract_test.schema import Schema, dump_schema_file


@pytest.fixture
def baseline_path(tmp_path: Path, minimal_openapi: dict[str, Any]) -> Path:
    path = tmp_path / "baseline.yaml"
    dump_schema_file(Schema(minimal_openapi), path)
    return path


@pytest.fixture
def current_path_no_breaking(tmp_path: Path, minimal_openapi: dict[str, Any]) -> Path:
    import copy

    current = copy.deepcopy(minimal_openapi)
    current["paths"]["/articles/"]["get"]["responses"]["200"]["content"]["application/json"][
        "schema"
    ] = {"$ref": "#/components/schemas/Article"}
    current["components"]["schemas"]["Article"]["properties"]["subtitle"] = {"type": "string"}
    path = tmp_path / "current-safe.yaml"
    dump_schema_file(Schema(current), path)
    return path


@pytest.fixture
def current_path_breaking(tmp_path: Path, minimal_openapi: dict[str, Any]) -> Path:
    import copy

    current = copy.deepcopy(minimal_openapi)
    del current["components"]["schemas"]["Article"]["properties"]["status"]
    current["components"]["schemas"]["Article"]["required"] = ["id", "title"]
    path = tmp_path / "current-breaking.yaml"
    dump_schema_file(Schema(current), path)
    return path


class TestCompare:
    def test_exits_zero_when_no_breaking_changes(
        self,
        baseline_path: Path,
        current_path_no_breaking: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        code = main(["compare", str(baseline_path), str(current_path_no_breaking)])
        assert code == 0
        out = capsys.readouterr().out
        assert "0 breaking change(s)" in out

    def test_exits_one_when_breaking_changes_present(
        self, baseline_path: Path, current_path_breaking: Path
    ) -> None:
        code = main(["compare", str(baseline_path), str(current_path_breaking)])
        assert code == 1

    def test_no_fail_on_breaking_flag(
        self, baseline_path: Path, current_path_breaking: Path
    ) -> None:
        code = main(
            ["compare", str(baseline_path), str(current_path_breaking), "--no-fail-on-breaking"]
        )
        assert code == 0

    def test_json_format(
        self, baseline_path: Path, current_path_breaking: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        main(["compare", str(baseline_path), str(current_path_breaking), "--format", "json"])
        payload = json.loads(capsys.readouterr().out)
        assert payload["summary"]["has_breaking_changes"] is True

    def test_output_file(
        self, baseline_path: Path, current_path_breaking: Path, tmp_path: Path
    ) -> None:
        out_path = tmp_path / "report.html"
        main(
            [
                "compare",
                str(baseline_path),
                str(current_path_breaking),
                "--format",
                "html",
                "--output",
                str(out_path),
            ]
        )
        assert out_path.exists()
        assert "<!doctype html>" in out_path.read_text(encoding="utf-8")

    def test_missing_baseline_file_reports_error(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        code = main(["compare", str(tmp_path / "missing.yaml"), str(tmp_path / "missing.yaml")])
        assert code == 2
        assert "error:" in capsys.readouterr().err


class TestCheck:
    def test_fails_when_breaking_changes_lack_version_bump(
        self, baseline_path: Path, current_path_breaking: Path
    ) -> None:
        code = main(["check", str(baseline_path), str(current_path_breaking)])
        assert code == 1

    def test_passes_when_version_bumped(
        self, tmp_path: Path, minimal_openapi: dict[str, Any]
    ) -> None:
        import copy

        baseline = tmp_path / "baseline.yaml"
        dump_schema_file(Schema(minimal_openapi), baseline)

        current = copy.deepcopy(minimal_openapi)
        del current["components"]["schemas"]["Article"]["properties"]["status"]
        current["components"]["schemas"]["Article"]["required"] = ["id", "title"]
        current["info"]["version"] = "2.0.0"
        current_path = tmp_path / "current.yaml"
        dump_schema_file(Schema(current), current_path)

        code = main(["check", str(baseline), str(current_path)])
        assert code == 0

    def test_require_major_bump_rejects_minor_bump(
        self, tmp_path: Path, minimal_openapi: dict[str, Any]
    ) -> None:
        import copy

        baseline = tmp_path / "baseline.yaml"
        dump_schema_file(Schema(minimal_openapi), baseline)

        current = copy.deepcopy(minimal_openapi)
        del current["components"]["schemas"]["Article"]["properties"]["status"]
        current["components"]["schemas"]["Article"]["required"] = ["id", "title"]
        current["info"]["version"] = "1.1.0"
        current_path = tmp_path / "current.yaml"
        dump_schema_file(Schema(current), current_path)

        code = main(["check", str(baseline), str(current_path), "--require-major-bump"])
        assert code == 1

    def test_no_fail_on_breaking_always_exits_zero(
        self, baseline_path: Path, current_path_breaking: Path
    ) -> None:
        code = main(
            ["check", str(baseline_path), str(current_path_breaking), "--no-fail-on-breaking"]
        )
        assert code == 0


class TestSnapshot:
    def test_writes_schema_file(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        out_path = tmp_path / "snapshot.json"
        code = main(
            [
                "snapshot",
                str(out_path),
                "--settings",
                "tests.test_app.settings",
                "--urlconf",
                "tests.test_app.urls",
            ]
        )
        assert code == 0
        assert out_path.exists()
        data = json.loads(out_path.read_text(encoding="utf-8"))
        assert "/articles/" in data["paths"]
        assert "Wrote schema snapshot" in capsys.readouterr().out


class TestArgparse:
    def test_missing_command_exits_nonzero(self) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main([])
        assert exc_info.value.code != 0
