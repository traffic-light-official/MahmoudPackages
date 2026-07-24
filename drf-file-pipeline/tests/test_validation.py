"""Tests for drf_file_pipeline.validation."""

from __future__ import annotations

import pytest
from django.test import override_settings

from drf_file_pipeline.exceptions import ValidationFailedError
from drf_file_pipeline.models import FileUpload
from drf_file_pipeline.validation import (
    run_custom_validators,
    validate_content_type,
    validate_size,
    validate_upload,
)

pytestmark = pytest.mark.django_db


class TestValidateContentType:
    def test_passes_when_no_restriction_configured(self) -> None:
        validate_content_type("anything/whatever")  # must not raise

    def test_passes_when_allowed(self) -> None:
        with override_settings(
            FILE_PIPELINE={"BUCKET_NAME": "b", "ALLOWED_CONTENT_TYPES": ["image/png"]}
        ):
            validate_content_type("image/png")

    def test_raises_when_not_allowed(self) -> None:
        with (
            override_settings(
                FILE_PIPELINE={"BUCKET_NAME": "b", "ALLOWED_CONTENT_TYPES": ["image/png"]}
            ),
            pytest.raises(ValidationFailedError),
        ):
            validate_content_type("application/x-msdownload")


class TestValidateSize:
    def test_passes_when_no_restriction_configured(self) -> None:
        validate_size(10_000_000_000)

    def test_passes_within_limit(self) -> None:
        with override_settings(FILE_PIPELINE={"BUCKET_NAME": "b", "MAX_UPLOAD_SIZE": 1000}):
            validate_size(500)

    def test_raises_over_limit(self) -> None:
        with (
            override_settings(FILE_PIPELINE={"BUCKET_NAME": "b", "MAX_UPLOAD_SIZE": 1000}),
            pytest.raises(ValidationFailedError),
        ):
            validate_size(1001)

    def test_passes_when_size_is_none(self) -> None:
        with override_settings(FILE_PIPELINE={"BUCKET_NAME": "b", "MAX_UPLOAD_SIZE": 1000}):
            validate_size(None)  # unknown size can't be checked; not a failure


def _reject_everything(upload: FileUpload) -> None:
    raise ValidationFailedError(f"{upload.original_filename} is always rejected.")


def _allow_everything(upload: FileUpload) -> None:
    pass


class TestCustomValidators:
    def test_no_callbacks_configured(self) -> None:
        upload = FileUpload.objects.create(
            key="uploads/a/file.txt", original_filename="file.txt", content_type="text/plain"
        )
        run_custom_validators(upload)  # must not raise

    def test_a_passing_callback(self) -> None:
        upload = FileUpload.objects.create(
            key="uploads/a/file.txt", original_filename="file.txt", content_type="text/plain"
        )
        with override_settings(
            FILE_PIPELINE={
                "BUCKET_NAME": "b",
                "VALIDATION_CALLBACKS": ["tests.test_validation._allow_everything"],
            }
        ):
            run_custom_validators(upload)

    def test_a_rejecting_callback(self) -> None:
        upload = FileUpload.objects.create(
            key="uploads/a/file.txt", original_filename="file.txt", content_type="text/plain"
        )
        with (
            override_settings(
                FILE_PIPELINE={
                    "BUCKET_NAME": "b",
                    "VALIDATION_CALLBACKS": ["tests.test_validation._reject_everything"],
                }
            ),
            pytest.raises(ValidationFailedError, match="always rejected"),
        ):
            run_custom_validators(upload)


class TestValidateUpload:
    def test_runs_every_check(self) -> None:
        upload = FileUpload.objects.create(
            key="uploads/a/file.exe",
            original_filename="file.exe",
            content_type="application/x-msdownload",
            size=2000,
        )
        with (
            override_settings(
                FILE_PIPELINE={
                    "BUCKET_NAME": "b",
                    "ALLOWED_CONTENT_TYPES": ["image/png"],
                    "MAX_UPLOAD_SIZE": 1000,
                }
            ),
            pytest.raises(ValidationFailedError),
        ):
            validate_upload(upload)
