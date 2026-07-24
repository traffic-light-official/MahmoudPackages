"""Upload validation: content-type/size checks, plus custom callbacks.

Validation runs twice: once when an upload is initiated (against the
client-declared filename/content-type/size, before any bytes exist),
and again during :func:`~drf_file_pipeline.processing.process_upload`
against the actual uploaded object — a client can lie about size or
content-type in the initiate request, so only the second pass is
authoritative.
"""

from __future__ import annotations

from django.utils.module_loading import import_string

from drf_file_pipeline.exceptions import ValidationFailedError
from drf_file_pipeline.models import FileUpload
from drf_file_pipeline.settings import get_setting


def validate_content_type(content_type: str) -> None:
    """Raise :class:`ValidationFailedError` if ``content_type`` isn't allowed."""
    allowed = get_setting("ALLOWED_CONTENT_TYPES")
    if allowed is not None and content_type not in allowed:
        raise ValidationFailedError(f"Content type {content_type!r} is not allowed.")


def validate_size(size: int | None) -> None:
    """Raise :class:`ValidationFailedError` if ``size`` exceeds ``MAX_UPLOAD_SIZE``."""
    max_size = get_setting("MAX_UPLOAD_SIZE")
    if max_size is not None and size is not None and size > max_size:
        raise ValidationFailedError(f"File size {size} exceeds the maximum of {max_size} bytes.")


def run_custom_validators(upload: FileUpload) -> None:
    """Run every callback in ``VALIDATION_CALLBACKS`` against ``upload``.

    Each callback is a ``(FileUpload) -> None`` dotted-path callable,
    expected to raise :class:`~drf_file_pipeline.exceptions.ValidationFailedError`
    to reject the upload.
    """
    for dotted_path in get_setting("VALIDATION_CALLBACKS"):
        callback = import_string(dotted_path)
        callback(upload)


def validate_upload(upload: FileUpload) -> None:
    """Run every configured validation check against ``upload``."""
    validate_content_type(upload.content_type)
    validate_size(upload.size)
    run_custom_validators(upload)
