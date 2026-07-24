"""DRF serializers for the upload lifecycle endpoints."""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from drf_file_pipeline.models import FileUpload, UploadPart, UploadStatus
from drf_file_pipeline.settings import get_setting
from drf_file_pipeline.storage import get_storage_backend
from drf_file_pipeline.validation import validate_content_type, validate_size


class InitiateUploadSerializer(serializers.Serializer[dict[str, Any]]):
    """Input for starting a new upload: what the client intends to send."""

    filename = serializers.CharField(max_length=255)
    content_type = serializers.CharField(max_length=255)
    size = serializers.IntegerField(min_value=0)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        validate_content_type(attrs["content_type"])
        validate_size(attrs["size"])
        return attrs


class UploadPartSerializer(serializers.ModelSerializer[UploadPart]):
    class Meta:
        model = UploadPart
        fields = ["part_number", "etag", "size", "uploaded_at"]
        read_only_fields = fields


class ReportPartSerializer(serializers.Serializer[dict[str, Any]]):
    """Input for reporting a completed multipart part's ETag back to the server."""

    part_number = serializers.IntegerField(min_value=1)
    etag = serializers.CharField(max_length=255)
    size = serializers.IntegerField(min_value=0)


class FileUploadSerializer(serializers.ModelSerializer[FileUpload]):
    """Read-only representation of an upload's current state."""

    parts = UploadPartSerializer(many=True, read_only=True)
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = FileUpload
        fields = [
            "id",
            "key",
            "original_filename",
            "content_type",
            "size",
            "status",
            "metadata",
            "error_message",
            "parts",
            "download_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_download_url(self, obj: FileUpload) -> str | None:
        if obj.status != UploadStatus.COMPLETED:
            return None
        storage = get_storage_backend()
        return storage.generate_presigned_get_url(
            key=obj.key, expiry=get_setting("PRESIGNED_DOWNLOAD_EXPIRY")
        )
