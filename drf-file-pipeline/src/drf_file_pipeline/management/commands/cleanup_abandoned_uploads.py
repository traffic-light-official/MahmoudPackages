"""Delete uploads that never completed, past a configurable age.

Run this periodically (a cron job, a Celery beat task, a Kubernetes
CronJob) to remove ``FileUpload`` rows — and their storage objects, for
multipart uploads that were left dangling — for uploads a client
initiated but never finished or explicitly aborted.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.core.management.base import BaseCommand
from django.utils import timezone

from drf_file_pipeline.models import FileUpload, UploadStatus
from drf_file_pipeline.settings import get_setting
from drf_file_pipeline.storage import get_storage_backend

_ABANDONED_STATUSES = (UploadStatus.PENDING, UploadStatus.UPLOADING)


class Command(BaseCommand):
    help = "Delete uploads stuck before completion past a configurable age."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--max-age-hours",
            type=int,
            default=None,
            help="Override FILE_PIPELINE['ABANDONED_UPLOAD_MAX_AGE_HOURS'] for this run.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List what would be deleted without deleting anything.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        max_age_hours = options["max_age_hours"] or get_setting("ABANDONED_UPLOAD_MAX_AGE_HOURS")
        cutoff = timezone.now() - timedelta(hours=max_age_hours)
        abandoned = list(
            FileUpload.objects.filter(status__in=_ABANDONED_STATUSES, created_at__lt=cutoff)
        )

        if not abandoned:
            self.stdout.write("No abandoned uploads found.")
            return

        if options["dry_run"]:
            for upload in abandoned:
                self.stdout.write(f"Would delete: {upload.pk} ({upload.original_filename})")
            self.stdout.write(f"{len(abandoned)} abandoned upload(s) would be deleted (dry run).")
            return

        storage = get_storage_backend()
        for upload in abandoned:
            if upload.is_multipart:
                assert upload.upload_id is not None  # guaranteed by is_multipart above
                storage.abort_multipart_upload(key=upload.key, upload_id=upload.upload_id)
            else:
                storage.delete(key=upload.key)
        deleted_ids = [upload.pk for upload in abandoned]
        deleted_count, _ = FileUpload.objects.filter(pk__in=deleted_ids).delete()
        self.stdout.write(f"Deleted {deleted_count} abandoned upload(s).")
