"""Storage abstraction: everything this package needs from an object store.

:class:`StorageBackend` is a :class:`typing.Protocol` — implement it for
GCS, Azure Blob, MinIO, or anything else with the same operations.
:class:`S3StorageBackend` is the built-in implementation, using
``boto3``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, cast

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

from drf_file_pipeline.exceptions import StorageError
from drf_file_pipeline.settings import get_setting

if TYPE_CHECKING:
    # boto3-stubs[s3] is a dev-only dependency — only import this for
    # type checking, never at runtime.
    from mypy_boto3_s3.type_defs import CompletedPartTypeDef


@dataclass(frozen=True, slots=True)
class PresignedPost:
    """A presigned ``POST`` upload target: the client posts the file plus these fields."""

    url: str
    fields: dict[str, str]


@dataclass(frozen=True, slots=True)
class ObjectInfo:
    """Metadata about an existing object in the store."""

    size: int
    content_type: str


class StorageBackend(Protocol):
    """Everything this package needs from an object store."""

    def create_presigned_post(
        self, *, key: str, content_type: str, max_size: int | None
    ) -> PresignedPost:
        """Build a presigned POST target for a single-request upload."""
        ...

    def create_multipart_upload(self, *, key: str, content_type: str) -> str:
        """Start a multipart upload, returning its upload id."""
        ...

    def presign_upload_part(self, *, key: str, upload_id: str, part_number: int) -> str:
        """Build a presigned URL the client can ``PUT`` one part's bytes to."""
        ...

    def complete_multipart_upload(
        self, *, key: str, upload_id: str, parts: list[dict[str, Any]]
    ) -> None:
        """Finish a multipart upload given ``[{"PartNumber": int, "ETag": str}, ...]``."""
        ...

    def abort_multipart_upload(self, *, key: str, upload_id: str) -> None:
        """Cancel an in-progress multipart upload and discard any uploaded parts."""
        ...

    def generate_presigned_get_url(self, *, key: str, expiry: int) -> str:
        """Build a time-limited, presigned download URL."""
        ...

    def delete(self, *, key: str) -> None:
        """Delete an object. Not an error if it doesn't exist."""
        ...

    def head(self, *, key: str) -> ObjectInfo | None:
        """Return metadata for an existing object, or ``None`` if it doesn't exist."""
        ...

    def download_to_path(self, *, key: str, path: str) -> None:
        """Download an object's bytes to a local path (used by image processing)."""
        ...

    def upload_from_path(self, *, key: str, path: str, content_type: str) -> None:
        """Upload a local file's bytes to a key (used to store generated presets)."""
        ...


class S3StorageBackend:
    """The built-in :class:`StorageBackend`, backed by Amazon S3 via ``boto3``."""

    def __init__(self, *, bucket_name: str | None = None, client: Any = None) -> None:
        self._bucket_name = bucket_name or get_setting("BUCKET_NAME")
        if not self._bucket_name:
            raise ImproperlyConfigured(
                "FILE_PIPELINE['BUCKET_NAME'] must be set to use S3StorageBackend."
            )
        self._client = client or boto3.client(
            "s3",
            region_name=get_setting("AWS_REGION"),
            config=Config(signature_version="s3v4"),
        )

    def create_presigned_post(
        self, *, key: str, content_type: str, max_size: int | None
    ) -> PresignedPost:
        conditions: list[Any] = [{"Content-Type": content_type}]
        if max_size is not None:
            conditions.append(["content-length-range", 0, max_size])
        try:
            result = self._client.generate_presigned_post(
                Bucket=self._bucket_name,
                Key=key,
                Fields={"Content-Type": content_type},
                Conditions=conditions,
                ExpiresIn=get_setting("PRESIGNED_UPLOAD_EXPIRY"),
            )
        except ClientError as exc:
            raise StorageError(f"Could not create presigned POST for {key!r}: {exc}") from exc
        return PresignedPost(url=result["url"], fields=result["fields"])

    def create_multipart_upload(self, *, key: str, content_type: str) -> str:
        try:
            result = self._client.create_multipart_upload(
                Bucket=self._bucket_name, Key=key, ContentType=content_type
            )
        except ClientError as exc:
            raise StorageError(f"Could not start multipart upload for {key!r}: {exc}") from exc
        upload_id: str = result["UploadId"]
        return upload_id

    def presign_upload_part(self, *, key: str, upload_id: str, part_number: int) -> str:
        try:
            url: str = self._client.generate_presigned_url(
                ClientMethod="upload_part",
                Params={
                    "Bucket": self._bucket_name,
                    "Key": key,
                    "UploadId": upload_id,
                    "PartNumber": part_number,
                },
                ExpiresIn=get_setting("PRESIGNED_UPLOAD_EXPIRY"),
            )
        except ClientError as exc:
            raise StorageError(f"Could not presign part {part_number} for {key!r}: {exc}") from exc
        return url

    def complete_multipart_upload(
        self, *, key: str, upload_id: str, parts: list[dict[str, Any]]
    ) -> None:
        try:
            self._client.complete_multipart_upload(
                Bucket=self._bucket_name,
                Key=key,
                UploadId=upload_id,
                MultipartUpload={"Parts": cast("list[CompletedPartTypeDef]", parts)},
            )
        except ClientError as exc:
            raise StorageError(f"Could not complete multipart upload for {key!r}: {exc}") from exc

    def abort_multipart_upload(self, *, key: str, upload_id: str) -> None:
        try:
            self._client.abort_multipart_upload(
                Bucket=self._bucket_name, Key=key, UploadId=upload_id
            )
        except ClientError as exc:
            raise StorageError(f"Could not abort multipart upload for {key!r}: {exc}") from exc

    def generate_presigned_get_url(self, *, key: str, expiry: int) -> str:
        try:
            url: str = self._client.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": self._bucket_name, "Key": key},
                ExpiresIn=expiry,
            )
        except ClientError as exc:
            raise StorageError(f"Could not presign a download URL for {key!r}: {exc}") from exc
        return url

    def delete(self, *, key: str) -> None:
        try:
            self._client.delete_object(Bucket=self._bucket_name, Key=key)
        except ClientError as exc:
            raise StorageError(f"Could not delete {key!r}: {exc}") from exc

    def head(self, *, key: str) -> ObjectInfo | None:
        try:
            result = self._client.head_object(Bucket=self._bucket_name, Key=key)
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code in ("404", "NoSuchKey"):
                return None
            raise StorageError(f"Could not inspect {key!r}: {exc}") from exc
        return ObjectInfo(size=result["ContentLength"], content_type=result.get("ContentType", ""))

    def download_to_path(self, *, key: str, path: str) -> None:
        try:
            self._client.download_file(self._bucket_name, key, path)
        except ClientError as exc:
            raise StorageError(f"Could not download {key!r}: {exc}") from exc

    def upload_from_path(self, *, key: str, path: str, content_type: str) -> None:
        try:
            self._client.upload_file(
                path, self._bucket_name, key, ExtraArgs={"ContentType": content_type}
            )
        except ClientError as exc:
            raise StorageError(f"Could not upload to {key!r}: {exc}") from exc


def get_storage_backend() -> StorageBackend:
    """Instantiate the configured :class:`StorageBackend` (``FILE_PIPELINE["STORAGE_BACKEND"]``)."""
    backend_cls = import_string(get_setting("STORAGE_BACKEND"))
    backend: StorageBackend = backend_cls()
    return backend
