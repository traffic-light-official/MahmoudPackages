"""Tests for drf_file_pipeline.permissions.IsUploadOwner."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from drf_file_pipeline.models import FileUpload
from drf_file_pipeline.permissions import IsUploadOwner

pytestmark = pytest.mark.django_db


class _Request:
    def __init__(self, user: object) -> None:
        self.user = user


class TestIsUploadOwner:
    def test_anonymous_owner_is_accessible_by_anyone(self) -> None:
        upload = FileUpload.objects.create(
            key="uploads/a/file.txt", original_filename="file.txt", content_type="text/plain"
        )
        request = _Request(AnonymousUser())
        assert IsUploadOwner().has_object_permission(request, None, upload) is True  # type: ignore[arg-type]

    def test_owner_can_access_own_upload(self) -> None:
        user = get_user_model().objects.create_user(username="alice")
        upload = FileUpload.objects.create(
            key="uploads/a/file.txt",
            original_filename="file.txt",
            content_type="text/plain",
            owner=user,
        )
        request = _Request(user)
        assert IsUploadOwner().has_object_permission(request, None, upload) is True  # type: ignore[arg-type]

    def test_other_user_cannot_access(self) -> None:
        alice = get_user_model().objects.create_user(username="alice")
        bob = get_user_model().objects.create_user(username="bob")
        upload = FileUpload.objects.create(
            key="uploads/a/file.txt",
            original_filename="file.txt",
            content_type="text/plain",
            owner=alice,
        )
        request = _Request(bob)
        assert IsUploadOwner().has_object_permission(request, None, upload) is False  # type: ignore[arg-type]

    def test_anonymous_user_cannot_access_owned_upload(self) -> None:
        alice = get_user_model().objects.create_user(username="alice")
        upload = FileUpload.objects.create(
            key="uploads/a/file.txt",
            original_filename="file.txt",
            content_type="text/plain",
            owner=alice,
        )
        request = _Request(AnonymousUser())
        assert IsUploadOwner().has_object_permission(request, None, upload) is False  # type: ignore[arg-type]
