"""End-to-end tests: real HTTP requests through the test app's URLconf."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from drf_file_pipeline.models import FileUpload, UploadStatus
from drf_file_pipeline.storage import S3StorageBackend

pytestmark = pytest.mark.django_db


class TestInitiateUpload:
    def test_small_file_gets_a_presigned_post(
        self, client: APIClient, storage: S3StorageBackend
    ) -> None:
        response = client.post(
            "/uploads/initiate/",
            data={"filename": "a.txt", "content_type": "text/plain", "size": 1000},
        )
        assert response.status_code == 201
        body = response.json()
        assert "presigned_post" in body
        assert "multipart" not in body
        assert body["upload"]["status"] == "uploading"

    def test_large_file_gets_multipart_upload(
        self, client: APIClient, storage: S3StorageBackend
    ) -> None:
        big_size = 50 * 1024 * 1024  # over the test settings' 10 MiB threshold
        response = client.post(
            "/uploads/initiate/",
            data={
                "filename": "big.bin",
                "content_type": "application/octet-stream",
                "size": big_size,
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert "multipart" in body
        assert body["multipart"]["upload_id"]
        assert len(body["multipart"]["parts"]) == 10  # 50MiB / 5MiB chunks

    def test_rejects_disallowed_content_type(
        self, client: APIClient, storage: S3StorageBackend, settings: object
    ) -> None:
        settings.FILE_PIPELINE = {  # type: ignore[attr-defined]
            "BUCKET_NAME": "test-bucket",
            "ALLOWED_CONTENT_TYPES": ["image/png"],
        }
        response = client.post(
            "/uploads/initiate/",
            data={"filename": "a.exe", "content_type": "application/x-msdownload", "size": 100},
        )
        assert response.status_code == 400

    def test_creates_upload_with_no_owner_for_anonymous_request(
        self, client: APIClient, storage: S3StorageBackend
    ) -> None:
        response = client.post(
            "/uploads/initiate/",
            data={"filename": "a.txt", "content_type": "text/plain", "size": 100},
        )
        upload_id = response.json()["upload"]["id"]
        assert FileUpload.objects.get(pk=upload_id).owner is None

    def test_owner_set_for_authenticated_request(
        self, client: APIClient, storage: S3StorageBackend
    ) -> None:
        user = get_user_model().objects.create_user(username="alice")
        client.force_authenticate(user)
        response = client.post(
            "/uploads/initiate/",
            data={"filename": "a.txt", "content_type": "text/plain", "size": 100},
        )
        upload_id = response.json()["upload"]["id"]
        assert FileUpload.objects.get(pk=upload_id).owner == user


class TestMultipartLifecycle:
    def test_full_multipart_flow(self, client: APIClient, storage: S3StorageBackend) -> None:
        big_size = 20 * 1024 * 1024
        initiate = client.post(
            "/uploads/initiate/",
            data={
                "filename": "big.bin",
                "content_type": "application/octet-stream",
                "size": big_size,
            },
        )
        upload_id = initiate.json()["upload"]["id"]
        upload = FileUpload.objects.get(pk=upload_id)
        assert upload.upload_id is not None

        # Simulate the client uploading each part directly to S3, then
        # reporting the resulting ETag back to our server.
        for part_number in range(1, 5):
            part_response = storage._client.upload_part(
                Bucket="test-bucket",
                Key=upload.key,
                UploadId=upload.upload_id,
                PartNumber=part_number,
                Body=b"x" * (5 * 1024 * 1024),
            )
            report = client.post(
                f"/uploads/{upload_id}/parts/",
                data={
                    "part_number": part_number,
                    "etag": part_response["ETag"],
                    "size": 5 * 1024 * 1024,
                },
            )
            assert report.status_code == 201

        complete = client.post(f"/uploads/{upload_id}/complete/")
        assert complete.status_code == 200
        assert complete.json()["status"] == "uploaded"

        upload.refresh_from_db()
        assert upload.status == UploadStatus.UPLOADED
        assert upload.parts.count() == 4

    def test_presign_part_for_resume(self, client: APIClient, storage: S3StorageBackend) -> None:
        initiate = client.post(
            "/uploads/initiate/",
            data={
                "filename": "big.bin",
                "content_type": "application/octet-stream",
                "size": 20 * 1024 * 1024,
            },
        )
        upload_id = initiate.json()["upload"]["id"]

        response = client.get(f"/uploads/{upload_id}/parts/2/presign/")
        assert response.status_code == 200
        assert response.json()["part_number"] == 2
        assert response.json()["url"].startswith("http")

    def test_presign_part_rejects_non_multipart_upload(
        self, client: APIClient, storage: S3StorageBackend
    ) -> None:
        initiate = client.post(
            "/uploads/initiate/",
            data={"filename": "a.txt", "content_type": "text/plain", "size": 100},
        )
        upload_id = initiate.json()["upload"]["id"]
        response = client.get(f"/uploads/{upload_id}/parts/1/presign/")
        assert response.status_code == 409


class TestCompleteUpload:
    def test_rejects_completing_a_non_uploading_upload(
        self, client: APIClient, storage: S3StorageBackend
    ) -> None:
        upload = FileUpload.objects.create(
            key="uploads/a/file.txt",
            original_filename="file.txt",
            content_type="text/plain",
            status=UploadStatus.COMPLETED,
        )
        response = client.post(f"/uploads/{upload.pk}/complete/")
        assert response.status_code == 409


class TestAbortUpload:
    def test_aborts_a_multipart_upload(self, client: APIClient, storage: S3StorageBackend) -> None:
        initiate = client.post(
            "/uploads/initiate/",
            data={
                "filename": "big.bin",
                "content_type": "application/octet-stream",
                "size": 20 * 1024 * 1024,
            },
        )
        upload_id = initiate.json()["upload"]["id"]

        response = client.post(f"/uploads/{upload_id}/abort/")
        assert response.status_code == 200
        assert response.json()["status"] == "aborted"

    def test_rejects_aborting_a_completed_upload(
        self, client: APIClient, storage: S3StorageBackend
    ) -> None:
        upload = FileUpload.objects.create(
            key="uploads/a/file.txt",
            original_filename="file.txt",
            content_type="text/plain",
            status=UploadStatus.COMPLETED,
        )
        response = client.post(f"/uploads/{upload.pk}/abort/")
        assert response.status_code == 409


class TestFileUploadViewSetPermissions:
    def test_owner_can_retrieve(self, client: APIClient, storage: S3StorageBackend) -> None:
        user = get_user_model().objects.create_user(username="alice")
        upload = FileUpload.objects.create(
            key="uploads/a/file.txt",
            original_filename="file.txt",
            content_type="text/plain",
            owner=user,
        )
        client.force_authenticate(user)
        response = client.get(f"/uploads/{upload.pk}/")
        assert response.status_code == 200

    def test_other_user_cannot_retrieve(self, client: APIClient, storage: S3StorageBackend) -> None:
        alice = get_user_model().objects.create_user(username="alice")
        bob = get_user_model().objects.create_user(username="bob")
        upload = FileUpload.objects.create(
            key="uploads/a/file.txt",
            original_filename="file.txt",
            content_type="text/plain",
            owner=alice,
        )
        client.force_authenticate(bob)
        response = client.get(f"/uploads/{upload.pk}/")
        assert response.status_code == 403

    def test_anonymous_owned_upload_is_retrievable_by_id(
        self, client: APIClient, storage: S3StorageBackend
    ) -> None:
        upload = FileUpload.objects.create(
            key="uploads/a/file.txt", original_filename="file.txt", content_type="text/plain"
        )
        response = client.get(f"/uploads/{upload.pk}/")
        assert response.status_code == 200

    def test_list_only_shows_own_uploads(
        self, client: APIClient, storage: S3StorageBackend
    ) -> None:
        alice = get_user_model().objects.create_user(username="alice")
        bob = get_user_model().objects.create_user(username="bob")
        FileUpload.objects.create(
            key="uploads/a/alice.txt",
            original_filename="alice.txt",
            content_type="text/plain",
            owner=alice,
        )
        FileUpload.objects.create(
            key="uploads/a/bob.txt",
            original_filename="bob.txt",
            content_type="text/plain",
            owner=bob,
        )
        client.force_authenticate(alice)
        response = client.get("/uploads/")
        filenames = {row["original_filename"] for row in response.json()}
        assert filenames == {"alice.txt"}

    def test_anonymous_list_is_empty(self, client: APIClient, storage: S3StorageBackend) -> None:
        FileUpload.objects.create(
            key="uploads/a/file.txt", original_filename="file.txt", content_type="text/plain"
        )
        response = client.get("/uploads/")
        assert response.json() == []
