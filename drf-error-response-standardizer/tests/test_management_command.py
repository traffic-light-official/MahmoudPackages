"""Tests for the ``generate_error_catalog`` management command."""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

from django.core.management import call_command


class TestGenerateErrorCatalogCommand:
    def test_default_format_is_markdown_to_stdout(self) -> None:
        out = StringIO()

        call_command("generate_error_catalog", stdout=out)

        assert "# Error Catalog" in out.getvalue()

    def test_json_format_to_stdout(self) -> None:
        out = StringIO()

        call_command("generate_error_catalog", format="json", stdout=out)

        parsed = json.loads(out.getvalue())
        assert any(entry["code"] == "validation_error" for entry in parsed)

    def test_writes_to_output_file_when_given(self, tmp_path: Path) -> None:
        out = StringIO()
        output_file = tmp_path / "catalog.md"

        call_command("generate_error_catalog", output=str(output_file), stdout=out)

        assert output_file.exists()
        assert "# Error Catalog" in output_file.read_text(encoding="utf-8")
        assert "Wrote" in out.getvalue()

    def test_writes_json_to_output_file(self, tmp_path: Path) -> None:
        output_file = tmp_path / "catalog.json"

        call_command("generate_error_catalog", format="json", output=str(output_file))

        parsed = json.loads(output_file.read_text(encoding="utf-8"))
        assert isinstance(parsed, list)
        assert len(parsed) > 0
