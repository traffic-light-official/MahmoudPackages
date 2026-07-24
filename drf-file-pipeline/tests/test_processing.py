"""Tests for drf_file_pipeline.processing.process_upload."""

from __future__ import annotations

from pathlib import Path

import pytest
from django.test import override_settings
from PIL import Image

from drf_file_pipeline.exceptions import InvalidUploadStateError
from drf_file_pipeline.models import FileUpload, UploadStatus
from drf_file_pipeline.processing import process_upload
from drf_file_pipeline.storage import S3StorageBackend

pytestmark = pytest.mark.django_db


def _create_uploaded_text_file(
    storage: S3StorageBackend, tmp_path: Path, content: bytes = b"hello"
) -> FileUpload:
    upload = FileUpload.objects.create(
        key="uploads/a/file.txt",
        original_filename="file.txt",
        content_type="text/plain",
        status=UploadStatus.UPLOADED,
    )
    source = tmp_path / "file.txt"
    source.write_bytes(content)
    storage.upload_from_path(key=upload.key, path=str(source), content_type="text/plain")
    return upload


class TestProcessUpload:
    def test_marks_completed_on_success(self, storage: S3StorageBackend, tmp_path: Path) -> None:
        upload = _create_uploaded_text_file(storage, tmp_path)

        result = process_upload(upload.pk)

        assert result.status == UploadStatus.COMPLETED
        assert result.error_message == ""
        assert result.size == len(b"hello")

    def test_rejects_wrong_starting_status(self, storage: S3StorageBackend) -> None:
        upload = FileUpload.objects.create(
            key="uploads/a/file.txt",
            original_filename="file.txt",
            content_type="text/plain",
            status=UploadStatus.PENDING,
        )
        with pytest.raises(InvalidUploadStateError):
            process_upload(upload.pk)

    def test_marks_failed_when_object_missing_from_storage(self, storage: S3StorageBackend) -> None:
        upload = FileUpload.objects.create(
            key="uploads/a/never-uploaded.txt",
            original_filename="never-uploaded.txt",
            content_type="text/plain",
            status=UploadStatus.UPLOADED,
        )
        result = process_upload(upload.pk)
        assert result.status == UploadStatus.FAILED
        assert "not found" in result.error_message

    def test_marks_failed_on_validation_failure(
        self, storage: S3StorageBackend, tmp_path: Path
    ) -> None:
        upload = _create_uploaded_text_file(storage, tmp_path)
        with override_settings(
            FILE_PIPELINE={"BUCKET_NAME": "test-bucket", "ALLOWED_CONTENT_TYPES": ["image/png"]}
        ):
            result = process_upload(upload.pk)
        assert result.status == UploadStatus.FAILED
        assert "not allowed" in result.error_message

    def test_marks_failed_on_virus_detection(
        self, storage: S3StorageBackend, tmp_path: Path
    ) -> None:
        upload = _create_uploaded_text_file(storage, tmp_path)
        with override_settings(
            FILE_PIPELINE={
                "BUCKET_NAME": "test-bucket",
                "VIRUS_SCAN_CALLBACK": "tests.test_virus_scan._infected_scanner",
            }
        ):
            result = process_upload(upload.pk)
        assert result.status == UploadStatus.FAILED
        assert "infected" in result.error_message

    def test_generates_image_presets_for_image_uploads(
        self, storage: S3StorageBackend, tmp_path: Path
    ) -> None:
        upload = FileUpload.objects.create(
            key="uploads/a/photo.png",
            original_filename="photo.png",
            content_type="image/png",
            status=UploadStatus.UPLOADED,
        )
        source = tmp_path / "photo.png"
        Image.new("RGB", (400, 300), color="green").save(source, format="PNG")
        storage.upload_from_path(key=upload.key, path=str(source), content_type="image/png")

        with override_settings(
            FILE_PIPELINE={
                "BUCKET_NAME": "test-bucket",
                "IMAGE_PRESETS": {"thumb": {"width": 50, "height": 50}},
            }
        ):
            result = process_upload(upload.pk)

        assert result.status == UploadStatus.COMPLETED
        assert result.metadata["presets"]["thumb"] == "uploads/a/photo__thumb.png"
        assert storage.head(key=result.metadata["presets"]["thumb"]) is not None

    def test_non_image_uploads_get_no_presets(
        self, storage: S3StorageBackend, tmp_path: Path
    ) -> None:
        upload = _create_uploaded_text_file(storage, tmp_path)
        with override_settings(
            FILE_PIPELINE={
                "BUCKET_NAME": "test-bucket",
                "IMAGE_PRESETS": {"thumb": {"width": 50, "height": 50}},
            }
        ):
            result = process_upload(upload.pk)
        assert result.status == UploadStatus.COMPLETED
        assert "presets" not in result.metadata

    def test_updates_size_from_actual_storage_object(
        self, storage: S3StorageBackend, tmp_path: Path
    ) -> None:
        # The client-declared size at initiate time can't be trusted;
        # process_upload() overwrites it with the real object size.
        upload = FileUpload.objects.create(
            key="uploads/a/file.txt",
            original_filename="file.txt",
            content_type="text/plain",
            size=999_999,  # a lie
            status=UploadStatus.UPLOADED,
        )
        source = tmp_path / "file.txt"
        source.write_bytes(b"actual contents")
        storage.upload_from_path(key=upload.key, path=str(source), content_type="text/plain")

        result = process_upload(upload.pk)
        assert result.size == len(b"actual contents")
