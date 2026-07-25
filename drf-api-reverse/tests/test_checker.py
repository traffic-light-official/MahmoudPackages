"""Tests for :mod:`drf_api_reverse.checker`."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from drf_api_reverse.checker import check_drift, raise_if_drifted
from drf_api_reverse.exceptions import DriftDetectedError
from drf_api_reverse.scaffolder import scaffold


class TestCheckDriftInSync:
    def test_freshly_scaffolded_output_has_no_drift(
        self, sample_schema: dict[str, Any], tmp_path: Path
    ) -> None:
        scaffold(sample_schema, tmp_path)
        reports = check_drift(sample_schema, tmp_path)
        assert all(not r.has_drift for r in reports)

    def test_reports_cover_all_three_files_in_order(
        self, sample_schema: dict[str, Any], tmp_path: Path
    ) -> None:
        scaffold(sample_schema, tmp_path)
        reports = check_drift(sample_schema, tmp_path)
        assert [r.filename for r in reports] == ["serializers.py", "views.py", "urls.py"]


class TestCheckDriftMissingFile:
    def test_missing_file_is_reported_as_drifted(
        self, sample_schema: dict[str, Any], tmp_path: Path
    ) -> None:
        reports = check_drift(sample_schema, tmp_path)
        assert all(r.file_missing for r in reports)
        assert all(r.has_drift for r in reports)

    def test_missing_file_lists_every_expected_region_as_missing(
        self, sample_schema: dict[str, Any], tmp_path: Path
    ) -> None:
        reports = check_drift(sample_schema, tmp_path)
        serializers_report = next(r for r in reports if r.filename == "serializers.py")
        assert set(serializers_report.missing_keys) == {
            "serializer:Author",
            "serializer:Article",
            "serializer:Comment",
        }


class TestCheckDriftSchemaChanged:
    def test_changed_schema_is_reported_as_changed(
        self, sample_schema: dict[str, Any], tmp_path: Path
    ) -> None:
        scaffold(sample_schema, tmp_path)
        changed_schema = {
            "components": {
                "schemas": {
                    **sample_schema["components"]["schemas"],
                    "Author": {
                        "type": "object",
                        "properties": {"nickname": {"type": "string"}},
                    },
                }
            },
            "paths": sample_schema["paths"],
        }

        reports = check_drift(changed_schema, tmp_path)

        serializers_report = next(r for r in reports if r.filename == "serializers.py")
        assert "serializer:Author" in serializers_report.changed_keys
        assert serializers_report.has_drift


class TestCheckDriftOrphaned:
    def test_removed_schema_entry_is_reported_as_orphaned(
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

        reports = check_drift(schema_without_comment, tmp_path)

        serializers_report = next(r for r in reports if r.filename == "serializers.py")
        assert "serializer:Comment" in serializers_report.orphaned_keys
        assert serializers_report.has_drift


class TestCheckDriftHandEditedRegion:
    def test_hand_editing_inside_a_region_is_detected_as_drift(
        self, sample_schema: dict[str, Any], tmp_path: Path
    ) -> None:
        scaffold(sample_schema, tmp_path)
        views_path = tmp_path / "views.py"
        text = views_path.read_text(encoding="utf-8")
        views_path.write_text(
            text.replace("raise NotImplementedError", "return None  #"), encoding="utf-8"
        )

        reports = check_drift(sample_schema, tmp_path)

        views_report = next(r for r in reports if r.filename == "views.py")
        assert views_report.has_drift
        assert views_report.changed_keys


class TestRaiseIfDrifted:
    def test_raises_when_drifted(self, sample_schema: dict[str, Any], tmp_path: Path) -> None:
        with pytest.raises(DriftDetectedError):
            raise_if_drifted(sample_schema, tmp_path)

    def test_does_not_raise_when_in_sync(
        self, sample_schema: dict[str, Any], tmp_path: Path
    ) -> None:
        scaffold(sample_schema, tmp_path)
        reports = raise_if_drifted(sample_schema, tmp_path)
        assert len(reports) == 3
