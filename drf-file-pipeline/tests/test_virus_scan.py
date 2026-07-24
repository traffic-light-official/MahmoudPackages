"""Tests for drf_file_pipeline.virus_scan."""

from __future__ import annotations

import pytest
from django.test import override_settings

from drf_file_pipeline.exceptions import VirusDetectedError
from drf_file_pipeline.models import FileUpload
from drf_file_pipeline.virus_scan import ScanResult, null_scanner, scan_upload

pytestmark = pytest.mark.django_db


def _infected_scanner(upload: FileUpload) -> ScanResult:
    return ScanResult(clean=False, details=f"{upload.original_filename} is infected.")


def _clean_scanner(upload: FileUpload) -> ScanResult:
    return ScanResult(clean=True)


class TestNullScanner:
    def test_always_reports_clean(self) -> None:
        upload = FileUpload.objects.create(
            key="uploads/a/file.txt", original_filename="file.txt", content_type="text/plain"
        )
        result = null_scanner(upload)
        assert result.clean is True
        assert result.details == ""


class TestScanUpload:
    def test_default_scanner_never_raises(self) -> None:
        upload = FileUpload.objects.create(
            key="uploads/a/file.txt", original_filename="file.txt", content_type="text/plain"
        )
        result = scan_upload(upload)
        assert result.clean is True

    def test_custom_scanner_can_raise(self) -> None:
        upload = FileUpload.objects.create(
            key="uploads/a/evil.exe",
            original_filename="evil.exe",
            content_type="application/x-msdownload",
        )
        with (
            override_settings(
                FILE_PIPELINE={
                    "BUCKET_NAME": "b",
                    "VIRUS_SCAN_CALLBACK": "tests.test_virus_scan._infected_scanner",
                }
            ),
            pytest.raises(VirusDetectedError, match="infected"),
        ):
            scan_upload(upload)

    def test_custom_clean_scanner(self) -> None:
        upload = FileUpload.objects.create(
            key="uploads/a/file.txt", original_filename="file.txt", content_type="text/plain"
        )
        with override_settings(
            FILE_PIPELINE={
                "BUCKET_NAME": "b",
                "VIRUS_SCAN_CALLBACK": "tests.test_virus_scan._clean_scanner",
            }
        ):
            result = scan_upload(upload)
        assert result.clean is True
