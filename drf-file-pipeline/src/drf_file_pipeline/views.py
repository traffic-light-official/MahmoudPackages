"""DRF views implementing the upload lifecycle.

``InitiateUploadView`` picks presigned-POST (small files) or presigned
multipart (large/resumable files) based on the declared size versus
``MULTIPART_THRESHOLD``. The client then uploads directly to storage,
reports each multipart part's ETag back via ``ReportPartView`` (so a
resumed upload can query which parts are already done), and finally
calls ``CompleteUploadView``.
"""

from __future__ import annotations

import math
import re
import uuid
from typing import Any

from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_file_pipeline.exceptions import InvalidUploadStateError
from drf_file_pipeline.models import FileUpload, UploadPart, UploadStatus
from drf_file_pipeline.permissions import IsUploadOwner
from drf_file_pipeline.serializers import (
    FileUploadSerializer,
    InitiateUploadSerializer,
    ReportPartSerializer,
)
from drf_file_pipeline.settings import get_setting
from drf_file_pipeline.storage import get_storage_backend

_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


def build_object_key(filename: str) -> str:
    """Build a unique, storage-safe object key for a new upload."""
    prefix = get_setting("KEY_PREFIX")
    safe_name = _UNSAFE_FILENAME_CHARS.sub("_", filename).strip("_") or "file"
    return f"{prefix}{uuid.uuid4()}/{safe_name}"


class InitiateUploadView(APIView):
    """``POST /uploads/`` — start a new upload, returning where to send the bytes.

    Open to anonymous requests by default (``owner`` is then ``None`` on
    the created upload) — this package's ownership model is designed to
    support anonymous upload flows (see ``IsUploadOwner``). Tighten this
    with your own ``permission_classes`` (e.g. ``IsAuthenticated``) if
    your application requires authentication to upload at all.
    """

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = InitiateUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        key = build_object_key(data["filename"])
        storage = get_storage_backend()
        owner = request.user if request.user.is_authenticated else None
        threshold = get_setting("MULTIPART_THRESHOLD")

        if data["size"] >= threshold:
            upload_id = storage.create_multipart_upload(key=key, content_type=data["content_type"])
            upload = FileUpload.objects.create(
                key=key,
                original_filename=data["filename"],
                content_type=data["content_type"],
                size=data["size"],
                status=UploadStatus.UPLOADING,
                upload_id=upload_id,
                owner=owner,
            )
            chunk_size = get_setting("MULTIPART_CHUNK_SIZE")
            num_parts = math.ceil(data["size"] / chunk_size)
            parts = [
                {
                    "part_number": part_number,
                    "url": storage.presign_upload_part(
                        key=key, upload_id=upload_id, part_number=part_number
                    ),
                }
                for part_number in range(1, num_parts + 1)
            ]
            payload: dict[str, Any] = {
                "upload": FileUploadSerializer(upload).data,
                "multipart": {"upload_id": upload_id, "chunk_size": chunk_size, "parts": parts},
            }
        else:
            presigned = storage.create_presigned_post(
                key=key, content_type=data["content_type"], max_size=get_setting("MAX_UPLOAD_SIZE")
            )
            upload = FileUpload.objects.create(
                key=key,
                original_filename=data["filename"],
                content_type=data["content_type"],
                size=data["size"],
                status=UploadStatus.UPLOADING,
                owner=owner,
            )
            payload = {
                "upload": FileUploadSerializer(upload).data,
                "presigned_post": {"url": presigned.url, "fields": presigned.fields},
            }

        return Response(payload, status=status.HTTP_201_CREATED)


class PresignPartView(APIView):
    """``GET /uploads/{pk}/parts/{part_number}/presign/`` — re-presign one part's upload URL.

    Used to resume a multipart upload whose original presigned URL for
    that part has expired.
    """

    permission_classes = [IsUploadOwner]

    def get(self, request: Request, pk: str, part_number: int) -> Response:
        upload = get_object_or_404(FileUpload, pk=pk)
        self.check_object_permissions(request, upload)
        if not upload.is_multipart:
            raise InvalidUploadStateError("This upload is not a multipart upload.")
        assert upload.upload_id is not None  # guaranteed by is_multipart above

        storage = get_storage_backend()
        url = storage.presign_upload_part(
            key=upload.key, upload_id=upload.upload_id, part_number=part_number
        )
        return Response({"part_number": part_number, "url": url})


class ReportPartView(APIView):
    """``POST /uploads/{pk}/parts/`` — record a completed multipart part's ETag.

    Lets the client (and this package) know which parts of a multipart
    upload are already done, so a resumed upload can skip re-uploading
    them — see ``FileUploadSerializer``'s ``parts`` field.
    """

    permission_classes = [IsUploadOwner]

    def post(self, request: Request, pk: str) -> Response:
        upload = get_object_or_404(FileUpload, pk=pk)
        self.check_object_permissions(request, upload)
        if not upload.is_multipart:
            raise InvalidUploadStateError("This upload is not a multipart upload.")

        serializer = ReportPartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        part, _ = UploadPart.objects.update_or_create(
            upload=upload,
            part_number=data["part_number"],
            defaults={"etag": data["etag"], "size": data["size"]},
        )
        return Response(
            {"part_number": part.part_number, "etag": part.etag, "size": part.size},
            status=status.HTTP_201_CREATED,
        )


class CompleteUploadView(APIView):
    """``POST /uploads/{pk}/complete/`` — finalize an upload.

    For a multipart upload, completes it in storage using every
    reported part's ETag. Marks the upload ``UPLOADED`` — actual
    validation, scanning, and preset generation happen in
    ``process_upload()``, called from your own background task queue.
    """

    permission_classes = [IsUploadOwner]

    def post(self, request: Request, pk: str) -> Response:
        upload = get_object_or_404(FileUpload, pk=pk)
        self.check_object_permissions(request, upload)
        if upload.status != UploadStatus.UPLOADING:
            raise InvalidUploadStateError(
                f"Cannot complete an upload in status {upload.status!r}; expected 'uploading'."
            )

        if upload.is_multipart:
            assert upload.upload_id is not None  # guaranteed by is_multipart above
            parts = [
                {"PartNumber": part.part_number, "ETag": part.etag}
                for part in upload.parts.order_by("part_number")
            ]
            storage = get_storage_backend()
            storage.complete_multipart_upload(
                key=upload.key, upload_id=upload.upload_id, parts=parts
            )

        upload.status = UploadStatus.UPLOADED
        upload.save(update_fields=["status", "updated_at"])
        return Response(FileUploadSerializer(upload).data)


class AbortUploadView(APIView):
    """``POST /uploads/{pk}/abort/`` — cancel an in-progress upload."""

    permission_classes = [IsUploadOwner]

    def post(self, request: Request, pk: str) -> Response:
        upload = get_object_or_404(FileUpload, pk=pk)
        self.check_object_permissions(request, upload)
        if upload.status not in (UploadStatus.PENDING, UploadStatus.UPLOADING):
            raise InvalidUploadStateError(f"Cannot abort an upload in status {upload.status!r}.")

        if upload.is_multipart:
            assert upload.upload_id is not None  # guaranteed by is_multipart above
            storage = get_storage_backend()
            storage.abort_multipart_upload(key=upload.key, upload_id=upload.upload_id)

        upload.status = UploadStatus.ABORTED
        upload.save(update_fields=["status", "updated_at"])
        return Response(FileUploadSerializer(upload).data)


class FileUploadViewSet(viewsets.ReadOnlyModelViewSet[FileUpload]):
    """Read-only list/detail of upload status, for polling progress."""

    queryset = FileUpload.objects.all()
    serializer_class = FileUploadSerializer
    permission_classes = [IsUploadOwner]

    def get_queryset(self) -> Any:
        qs = super().get_queryset()
        if self.action != "list":
            # Detail access is enforced by IsUploadOwner.has_object_permission
            # (which also allows anonymous-owned uploads by id) — don't
            # pre-filter here, or an anonymous upload could never be
            # retrieved even by someone who knows its id.
            return qs
        if self.request.user.is_authenticated:
            return qs.filter(owner=self.request.user)
        return qs.none()
