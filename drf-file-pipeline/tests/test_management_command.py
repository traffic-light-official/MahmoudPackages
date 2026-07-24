"""Tests for the cleanup_abandoned_uploads management command."""

from __future__ import annotations

import io
from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone

from drf_file_pipeline.models import FileUpload, UploadStatus
from drf_file_pipeline.storage import S3StorageBackend

pytestmark = pytest.mark.django_db


def _make_upload(*, status: str, age_hours: float, upload_id: str | None = None) -> FileUpload:
    upload = FileUpload.objects.create(
        key=f"uploads/a/{status}-{age_hours}.txt",
        original_filename="file.txt",
        content_type="text/plain",
        status=status,
        upload_id=upload_id,
    )
    FileUpload.objects.filter(pk=upload.pk).update(
        created_at=timezone.now() - timedelta(hours=age_hours)
    )
    upload.refresh_from_db()
    return upload


class TestCleanupAbandonedUploads:
    def test_deletes_old_pending_and_uploading_uploads(self, storage: S3StorageBackend) -> None:
        old_pending = _make_upload(status=UploadStatus.PENDING, age_hours=48)
        old_uploading = _make_upload(status=UploadStatus.UPLOADING, age_hours=48)

        out = io.StringIO()
        call_command("cleanup_abandoned_uploads", stdout=out)

        assert not FileUpload.objects.filter(pk=old_pending.pk).exists()
        assert not FileUpload.objects.filter(pk=old_uploading.pk).exists()
        assert "Deleted 2 abandoned upload(s)." in out.getvalue()

    def test_leaves_recent_uploads_alone(self, storage: S3StorageBackend) -> None:
        recent = _make_upload(status=UploadStatus.PENDING, age_hours=1)

        call_command("cleanup_abandoned_uploads", stdout=io.StringIO())

        assert FileUpload.objects.filter(pk=recent.pk).exists()

    def test_leaves_completed_uploads_alone_regardless_of_age(
        self, storage: S3StorageBackend
    ) -> None:
        completed = _make_upload(status=UploadStatus.COMPLETED, age_hours=1000)

        call_command("cleanup_abandoned_uploads", stdout=io.StringIO())

        assert FileUpload.objects.filter(pk=completed.pk).exists()

    def test_dry_run_does_not_delete(self, storage: S3StorageBackend) -> None:
        old_pending = _make_upload(status=UploadStatus.PENDING, age_hours=48)

        out = io.StringIO()
        call_command("cleanup_abandoned_uploads", "--dry-run", stdout=out)

        assert FileUpload.objects.filter(pk=old_pending.pk).exists()
        assert "would be deleted" in out.getvalue()

    def test_no_abandoned_uploads(self, storage: S3StorageBackend) -> None:
        out = io.StringIO()
        call_command("cleanup_abandoned_uploads", stdout=out)
        assert "No abandoned uploads found." in out.getvalue()

    def test_max_age_override(self, storage: S3StorageBackend) -> None:
        upload = _make_upload(status=UploadStatus.PENDING, age_hours=2)

        out = io.StringIO()
        call_command("cleanup_abandoned_uploads", "--max-age-hours=1", stdout=out)

        assert not FileUpload.objects.filter(pk=upload.pk).exists()

    def test_aborts_multipart_upload_in_storage(self, storage: S3StorageBackend) -> None:
        key = "uploads/a/abandoned-multipart.bin"
        upload_id = storage.create_multipart_upload(
            key=key, content_type="application/octet-stream"
        )
        upload = FileUpload.objects.create(
            key=key,
            original_filename="abandoned-multipart.bin",
            content_type="application/octet-stream",
            status=UploadStatus.UPLOADING,
            upload_id=upload_id,
        )
        FileUpload.objects.filter(pk=upload.pk).update(
            created_at=timezone.now() - timedelta(hours=48)
        )

        call_command("cleanup_abandoned_uploads", stdout=io.StringIO())

        assert not FileUpload.objects.filter(pk=upload.pk).exists()
        # The multipart upload should have been aborted in storage too,
        # not left dangling and billed forever.
        remaining = storage._client.list_multipart_uploads(Bucket="test-bucket")
        in_progress_ids = {u["UploadId"] for u in remaining.get("Uploads", [])}
        assert upload_id not in in_progress_ids
