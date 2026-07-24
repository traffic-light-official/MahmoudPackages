"""Custom exceptions raised by :mod:`drf_file_pipeline`."""

from __future__ import annotations

from rest_framework import status
from rest_framework.exceptions import APIException


class FilePipelineError(Exception):
    """Base class for all errors raised by this package."""


class StorageError(FilePipelineError):
    """Raised when the configured storage backend fails (an S3 API error, etc.)."""


class ValidationFailedError(APIException, FilePipelineError):
    """Raised when a configured validation callback rejects an upload."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The file failed validation."
    default_code = "file_validation_failed"


class VirusDetectedError(APIException, FilePipelineError):
    """Raised when the configured virus-scan callback flags an upload as infected."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The file failed a virus scan."
    default_code = "virus_detected"


class InvalidUploadStateError(APIException, FilePipelineError):
    """Raised when an operation is attempted against an upload in the wrong status."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "This operation is not valid for the upload's current status."
    default_code = "invalid_upload_state"
