"""Models tracking upload lifecycle state."""

from __future__ import annotations

import uuid
from typing import Any

from django.conf import settings
from django.db import models

from drf_file_pipeline.settings import get_setting


class UploadStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    UPLOADING = "uploading", "Uploading"
    UPLOADED = "uploaded", "Uploaded"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"
    ABORTED = "aborted", "Aborted"


class FileUpload(models.Model):
    """A single tracked upload, from presign to (eventually) completion."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=1024, unique=True)
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=255)
    size = models.BigIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=UploadStatus.choices, default=UploadStatus.PENDING
    )
    upload_id = models.CharField(max_length=255, null=True, blank=True)
    checksum = models.CharField(max_length=128, null=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="file_uploads",
    )
    metadata: models.JSONField[dict[str, Any]] = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.original_filename} ({self.status})"

    @property
    def is_multipart(self) -> bool:
        return bool(self.upload_id)

    @property
    def is_image(self) -> bool:
        prefix: str = get_setting("IMAGE_CONTENT_TYPE_PREFIX")
        return self.content_type.startswith(prefix)


class UploadPart(models.Model):
    """A single completed part of a multipart upload, for resumability."""

    upload = models.ForeignKey(FileUpload, on_delete=models.CASCADE, related_name="parts")
    part_number = models.PositiveIntegerField()
    etag = models.CharField(max_length=255)
    size = models.BigIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["part_number"]
        constraints = [
            models.UniqueConstraint(fields=["upload", "part_number"], name="unique_upload_part")
        ]
