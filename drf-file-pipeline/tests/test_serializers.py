"""Tests for drf_file_pipeline.serializers."""

from __future__ import annotations

import pytest
from django.test import override_settings

from drf_file_pipeline.exceptions import ValidationFailedError
from drf_file_pipeline.models import FileUpload, UploadPart, UploadStatus
from drf_file_pipeline.serializers import FileUploadSerializer, InitiateUploadSerializer
from drf_file_pipeline.storage import S3StorageBackend

pytestmark = pytest.mark.django_db


class TestInitiateUploadSerializer:
    def test_valid_input(self) -> None:
        serializer = InitiateUploadSerializer(
            data={"filename": "a.txt", "content_type": "text/plain", "size": 100}
        )
        assert serializer.is_valid(), serializer.errors

    def test_rejects_disallowed_content_type(self) -> None:
        with override_settings(
            FILE_PIPELINE={"BUCKET_NAME": "b", "ALLOWED_CONTENT_TYPES": ["image/png"]}
        ):
            serializer = InitiateUploadSerializer(
                data={"filename": "a.exe", "content_type": "application/x-msdownload", "size": 100}
            )
            with pytest.raises(ValidationFailedError):
                serializer.is_valid(raise_exception=True)

    def test_rejects_oversized_declared_size(self) -> None:
        with override_settings(FILE_PIPELINE={"BUCKET_NAME": "b", "MAX_UPLOAD_SIZE": 100}):
            serializer = InitiateUploadSerializer(
                data={"filename": "a.txt", "content_type": "text/plain", "size": 101}
            )
            with pytest.raises(ValidationFailedError):
                serializer.is_valid(raise_exception=True)

    def test_rejects_negative_size(self) -> None:
        serializer = InitiateUploadSerializer(
            data={"filename": "a.txt", "content_type": "text/plain", "size": -1}
        )
        assert not serializer.is_valid()
        assert "size" in serializer.errors


class TestFileUploadSerializer:
    def test_download_url_none_when_not_completed(self) -> None:
        upload = FileUpload.objects.create(
            key="uploads/a/file.txt",
            original_filename="file.txt",
            content_type="text/plain",
            status=UploadStatus.UPLOADING,
        )
        data = FileUploadSerializer(upload).data
        assert data["download_url"] is None

    def test_download_url_present_when_completed(self, storage: S3StorageBackend) -> None:
        upload = FileUpload.objects.create(
            key="uploads/a/file.txt",
            original_filename="file.txt",
            content_type="text/plain",
            status=UploadStatus.COMPLETED,
        )
        data = FileUploadSerializer(upload).data
        assert data["download_url"].startswith("http")

    def test_includes_parts(self, storage: S3StorageBackend) -> None:
        upload = FileUpload.objects.create(
            key="uploads/a/file.txt",
            original_filename="file.txt",
            content_type="text/plain",
            status=UploadStatus.UPLOADING,
            upload_id="abc",
        )
        UploadPart.objects.create(upload=upload, part_number=1, etag="e1", size=100)
        data = FileUploadSerializer(upload).data
        assert len(data["parts"]) == 1
        assert data["parts"][0]["part_number"] == 1
