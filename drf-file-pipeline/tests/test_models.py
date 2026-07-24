"""Tests for drf_file_pipeline.models."""

from __future__ import annotations

import pytest
from django.db import IntegrityError
from django.test import override_settings

from drf_file_pipeline.models import FileUpload, UploadPart, UploadStatus

pytestmark = pytest.mark.django_db


class TestFileUpload:
    def test_str(self) -> None:
        upload = FileUpload.objects.create(
            key="uploads/a/file.txt", original_filename="file.txt", content_type="text/plain"
        )
        assert str(upload) == "file.txt (pending)"

    def test_defaults(self) -> None:
        upload = FileUpload.objects.create(
            key="uploads/a/file.txt", original_filename="file.txt", content_type="text/plain"
        )
        assert upload.status == UploadStatus.PENDING
        assert upload.size is None
        assert upload.upload_id is None
        assert upload.metadata == {}
        assert upload.error_message == ""

    def test_is_multipart(self) -> None:
        upload = FileUpload.objects.create(
            key="uploads/a/file.txt",
            original_filename="file.txt",
            content_type="text/plain",
            upload_id="abc123",
        )
        assert upload.is_multipart is True

        upload2 = FileUpload.objects.create(
            key="uploads/a/file2.txt", original_filename="file2.txt", content_type="text/plain"
        )
        assert upload2.is_multipart is False

    def test_is_image(self) -> None:
        image = FileUpload.objects.create(
            key="uploads/a/photo.png", original_filename="photo.png", content_type="image/png"
        )
        assert image.is_image is True

        doc = FileUpload.objects.create(
            key="uploads/a/doc.pdf", original_filename="doc.pdf", content_type="application/pdf"
        )
        assert doc.is_image is False

    def test_is_image_honors_custom_prefix_setting(self) -> None:
        upload = FileUpload.objects.create(
            key="uploads/a/file.raw", original_filename="file.raw", content_type="raw/nef"
        )
        with override_settings(
            FILE_PIPELINE={"BUCKET_NAME": "b", "IMAGE_CONTENT_TYPE_PREFIX": "raw/"}
        ):
            assert upload.is_image is True

    def test_key_must_be_unique(self) -> None:
        FileUpload.objects.create(
            key="uploads/a/dup.txt", original_filename="dup.txt", content_type="text/plain"
        )
        with pytest.raises(IntegrityError):
            FileUpload.objects.create(
                key="uploads/a/dup.txt", original_filename="dup2.txt", content_type="text/plain"
            )


class TestUploadPart:
    def test_unique_part_number_per_upload(self) -> None:
        upload = FileUpload.objects.create(
            key="uploads/a/file.txt", original_filename="file.txt", content_type="text/plain"
        )
        UploadPart.objects.create(upload=upload, part_number=1, etag="e1", size=100)
        with pytest.raises(IntegrityError):
            UploadPart.objects.create(upload=upload, part_number=1, etag="e2", size=200)

    def test_ordering(self) -> None:
        upload = FileUpload.objects.create(
            key="uploads/a/file.txt", original_filename="file.txt", content_type="text/plain"
        )
        UploadPart.objects.create(upload=upload, part_number=2, etag="e2", size=100)
        UploadPart.objects.create(upload=upload, part_number=1, etag="e1", size=100)
        assert list(upload.parts.values_list("part_number", flat=True)) == [1, 2]
