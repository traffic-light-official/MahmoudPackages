"""Tests for drf_file_pipeline.storage.S3StorageBackend, against a mocked S3 (moto)."""

from __future__ import annotations

from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured

from drf_file_pipeline.exceptions import StorageError
from drf_file_pipeline.storage import ObjectInfo, PresignedPost, S3StorageBackend


class TestPresignedPost:
    def test_returns_url_and_fields(self, storage: S3StorageBackend) -> None:
        result = storage.create_presigned_post(
            key="uploads/a/file.txt", content_type="text/plain", max_size=1000
        )
        assert isinstance(result, PresignedPost)
        assert result.url
        assert "key" in result.fields

    def test_without_max_size(self, storage: S3StorageBackend) -> None:
        result = storage.create_presigned_post(
            key="uploads/a/file.txt", content_type="text/plain", max_size=None
        )
        assert result.url


class TestMultipartUpload:
    def test_full_lifecycle(self, storage: S3StorageBackend) -> None:
        key = "uploads/a/big.bin"
        upload_id = storage.create_multipart_upload(
            key=key, content_type="application/octet-stream"
        )
        assert upload_id

        url = storage.presign_upload_part(key=key, upload_id=upload_id, part_number=1)
        assert url

        # Simulate the client's direct-to-S3 part upload via the boto3
        # client directly (see tests/conftest.py's `storage` fixture) —
        # this tests our state tracking and orchestration, not whether a
        # raw HTTP PUT against a presigned URL succeeds (that's AWS's own
        # contract, not this package's).
        part_response = storage._client.upload_part(
            Bucket=storage._bucket_name,
            Key=key,
            UploadId=upload_id,
            PartNumber=1,
            Body=b"x" * (5 * 1024 * 1024),
        )
        etag = part_response["ETag"]

        storage.complete_multipart_upload(
            key=key, upload_id=upload_id, parts=[{"PartNumber": 1, "ETag": etag}]
        )

        info = storage.head(key=key)
        assert info is not None
        assert info.size == 5 * 1024 * 1024

    def test_abort(self, storage: S3StorageBackend) -> None:
        key = "uploads/a/aborted.bin"
        upload_id = storage.create_multipart_upload(
            key=key, content_type="application/octet-stream"
        )
        storage.abort_multipart_upload(key=key, upload_id=upload_id)
        assert storage.head(key=key) is None


class TestHeadAndDelete:
    def test_head_returns_none_for_missing_key(self, storage: S3StorageBackend) -> None:
        assert storage.head(key="uploads/does/not/exist") is None

    def test_head_returns_object_info(self, storage: S3StorageBackend, tmp_path: Path) -> None:
        source = tmp_path / "hello.txt"
        source.write_bytes(b"hello world")
        storage.upload_from_path(
            key="uploads/a/hello.txt", path=str(source), content_type="text/plain"
        )

        info = storage.head(key="uploads/a/hello.txt")
        assert isinstance(info, ObjectInfo)
        assert info.size == len(b"hello world")
        assert info.content_type == "text/plain"

    def test_delete_is_not_an_error_for_missing_key(self, storage: S3StorageBackend) -> None:
        storage.delete(key="uploads/does/not/exist")  # must not raise


class TestDownloadAndUpload:
    def test_roundtrip(self, storage: S3StorageBackend, tmp_path: Path) -> None:
        source = tmp_path / "source.txt"
        source.write_bytes(b"round trip contents")
        storage.upload_from_path(
            key="uploads/a/roundtrip.txt", path=str(source), content_type="text/plain"
        )

        dest = tmp_path / "dest.txt"
        storage.download_to_path(key="uploads/a/roundtrip.txt", path=str(dest))
        assert dest.read_bytes() == b"round trip contents"


class TestPresignedGetUrl:
    def test_returns_a_url(self, storage: S3StorageBackend) -> None:
        url = storage.generate_presigned_get_url(key="uploads/a/file.txt", expiry=300)
        assert url.startswith("http")


class TestConstructorValidation:
    def test_raises_without_bucket_name(self, settings: object) -> None:
        settings.FILE_PIPELINE = {}  # type: ignore[attr-defined]
        with pytest.raises(ImproperlyConfigured, match="BUCKET_NAME"):
            S3StorageBackend()


def _raise_client_error(operation_name: str, code: str = "500") -> object:
    from botocore.exceptions import ClientError

    def boom(*args: object, **kwargs: object) -> None:
        raise ClientError({"Error": {"Code": code, "Message": "boom"}}, operation_name)

    return boom


class TestErrorWrapping:
    def test_delete_error_is_wrapped(
        self, storage: S3StorageBackend, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(storage._client, "delete_object", _raise_client_error("DeleteObject"))
        with pytest.raises(StorageError):
            storage.delete(key="uploads/a/file.txt")

    def test_create_presigned_post_error_is_wrapped(
        self, storage: S3StorageBackend, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            storage._client, "generate_presigned_post", _raise_client_error("PostObject")
        )
        with pytest.raises(StorageError):
            storage.create_presigned_post(key="k", content_type="text/plain", max_size=None)

    def test_create_multipart_upload_error_is_wrapped(
        self, storage: S3StorageBackend, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            storage._client, "create_multipart_upload", _raise_client_error("CreateMultipartUpload")
        )
        with pytest.raises(StorageError):
            storage.create_multipart_upload(key="k", content_type="text/plain")

    def test_presign_upload_part_error_is_wrapped(
        self, storage: S3StorageBackend, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            storage._client, "generate_presigned_url", _raise_client_error("UploadPart")
        )
        with pytest.raises(StorageError):
            storage.presign_upload_part(key="k", upload_id="u", part_number=1)

    def test_complete_multipart_upload_error_is_wrapped(
        self, storage: S3StorageBackend, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            storage._client,
            "complete_multipart_upload",
            _raise_client_error("CompleteMultipartUpload"),
        )
        with pytest.raises(StorageError):
            storage.complete_multipart_upload(key="k", upload_id="u", parts=[])

    def test_abort_multipart_upload_error_is_wrapped(
        self, storage: S3StorageBackend, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            storage._client, "abort_multipart_upload", _raise_client_error("AbortMultipartUpload")
        )
        with pytest.raises(StorageError):
            storage.abort_multipart_upload(key="k", upload_id="u")

    def test_generate_presigned_get_url_error_is_wrapped(
        self, storage: S3StorageBackend, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            storage._client, "generate_presigned_url", _raise_client_error("GetObject")
        )
        with pytest.raises(StorageError):
            storage.generate_presigned_get_url(key="k", expiry=60)

    def test_head_non_404_error_is_wrapped(
        self, storage: S3StorageBackend, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            storage._client, "head_object", _raise_client_error("HeadObject", code="500")
        )
        with pytest.raises(StorageError):
            storage.head(key="k")

    def test_download_to_path_error_is_wrapped(
        self, storage: S3StorageBackend, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(storage._client, "download_file", _raise_client_error("GetObject"))
        with pytest.raises(StorageError):
            storage.download_to_path(key="k", path="/tmp/x")

    def test_upload_from_path_error_is_wrapped(
        self, storage: S3StorageBackend, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        source = tmp_path / "f.txt"
        source.write_bytes(b"x")
        monkeypatch.setattr(storage._client, "upload_file", _raise_client_error("PutObject"))
        with pytest.raises(StorageError):
            storage.upload_from_path(key="k", path=str(source), content_type="text/plain")
