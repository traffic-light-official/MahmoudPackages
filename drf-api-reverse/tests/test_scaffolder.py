"""Tests for :mod:`drf_api_reverse.scaffolder`."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from drf_api_reverse.scaffolder import scaffold


class TestScaffoldCreatesFiles:
    def test_creates_all_three_files(self, sample_schema: dict[str, Any], tmp_path: Path) -> None:
        results = scaffold(sample_schema, tmp_path)

        assert [r.filename for r in results] == ["serializers.py", "views.py", "urls.py"]
        assert all(r.created for r in results)
        assert (tmp_path / "serializers.py").exists()
        assert (tmp_path / "views.py").exists()
        assert (tmp_path / "urls.py").exists()

    def test_creates_the_output_directory_if_missing(
        self, sample_schema: dict[str, Any], tmp_path: Path
    ) -> None:
        output_dir = tmp_path / "nested" / "app"
        scaffold(sample_schema, output_dir)
        assert (output_dir / "serializers.py").exists()

    def test_generated_files_are_valid_python(
        self, sample_schema: dict[str, Any], tmp_path: Path
    ) -> None:
        scaffold(sample_schema, tmp_path)
        for filename in ("serializers.py", "views.py", "urls.py"):
            compile((tmp_path / filename).read_text(encoding="utf-8"), filename, "exec")


class TestScaffoldRegeneration:
    def test_second_run_updates_rather_than_creates(
        self, sample_schema: dict[str, Any], tmp_path: Path
    ) -> None:
        scaffold(sample_schema, tmp_path)
        results = scaffold(sample_schema, tmp_path)
        assert all(not r.created for r in results)

    def test_hand_written_code_survives_regeneration(
        self, sample_schema: dict[str, Any], tmp_path: Path
    ) -> None:
        scaffold(sample_schema, tmp_path)
        views_path = tmp_path / "views.py"
        views_path.write_text(
            views_path.read_text(encoding="utf-8") + "\n\ndef my_helper():\n    return 42\n",
            encoding="utf-8",
        )

        scaffold(sample_schema, tmp_path)

        assert "def my_helper():" in views_path.read_text(encoding="utf-8")

    def test_schema_change_updates_only_the_affected_region(
        self, sample_schema: dict[str, Any], tmp_path: Path
    ) -> None:
        scaffold(sample_schema, tmp_path)
        changed_schema = {
            "components": {
                "schemas": {
                    **sample_schema["components"]["schemas"],
                    "Author": {
                        **sample_schema["components"]["schemas"]["Author"],
                        "properties": {
                            **sample_schema["components"]["schemas"]["Author"]["properties"],
                            "bio": {"type": "string"},
                        },
                    },
                }
            },
            "paths": sample_schema["paths"],
        }

        scaffold(changed_schema, tmp_path)

        serializers_text = (tmp_path / "serializers.py").read_text(encoding="utf-8")
        assert "bio = serializers.CharField(required=False)" in serializers_text

    def test_removed_schema_leaves_an_orphaned_region_in_place(
        self, sample_schema: dict[str, Any], tmp_path: Path
    ) -> None:
        scaffold(sample_schema, tmp_path)
        schema_without_comment = {
            "components": {
                "schemas": {
                    k: v
                    for k, v in sample_schema["components"]["schemas"].items()
                    if k != "Comment"
                }
            },
            "paths": sample_schema["paths"],
        }

        results = scaffold(schema_without_comment, tmp_path)

        serializers_result = next(r for r in results if r.filename == "serializers.py")
        assert "serializer:Comment" in serializers_result.orphaned_keys
        assert "class CommentSerializer" in (tmp_path / "serializers.py").read_text(
            encoding="utf-8"
        )
