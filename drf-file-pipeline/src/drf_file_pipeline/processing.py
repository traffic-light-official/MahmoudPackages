"""The single background-processing entry point for a completed upload.

:func:`process_upload` is deliberately a plain function with no
dependency on any particular task queue — call it from a Celery task, an
RQ job, a Huey task, or a management-command polling loop. This package
does not ship a worker of its own; wiring it into whatever you already
run is one line:

.. code-block:: python

    @shared_task
    def process_upload_task(upload_id):
        from drf_file_pipeline.processing import process_upload
        process_upload(upload_id)
"""

from __future__ import annotations

import uuid

from drf_file_pipeline.exceptions import FilePipelineError, InvalidUploadStateError, StorageError
from drf_file_pipeline.images import generate_image_presets
from drf_file_pipeline.models import FileUpload, UploadStatus
from drf_file_pipeline.storage import get_storage_backend
from drf_file_pipeline.validation import validate_upload
from drf_file_pipeline.virus_scan import scan_upload


def process_upload(upload_id: uuid.UUID | str) -> FileUpload:
    """Validate, scan, and (for images) generate presets for a completed upload.

    Transitions ``upload.status`` through ``PROCESSING`` to either
    ``COMPLETED`` or ``FAILED`` (with ``error_message`` set), and
    persists every transition.

    Args:
        upload_id: Primary key of the :class:`~drf_file_pipeline.models.FileUpload`
            to process. Must currently be in ``UPLOADED`` status.

    Returns:
        The updated :class:`~drf_file_pipeline.models.FileUpload`.

    Raises:
        drf_file_pipeline.exceptions.InvalidUploadStateError: If the
            upload isn't in ``UPLOADED`` status. This is a caller error
            (processing something not ready to be processed), so it
            raises rather than marking the upload failed.
    """
    upload = FileUpload.objects.get(pk=upload_id)
    if upload.status != UploadStatus.UPLOADED:
        raise InvalidUploadStateError(
            f"Cannot process upload {upload_id} in status {upload.status!r}; "
            f"expected {UploadStatus.UPLOADED!r}."
        )

    upload.status = UploadStatus.PROCESSING
    upload.save(update_fields=["status", "updated_at"])

    storage = get_storage_backend()
    try:
        info = storage.head(key=upload.key)
        if info is None:
            raise StorageError(f"Object {upload.key!r} was not found in storage.")
        upload.size = info.size

        validate_upload(upload)
        scan_upload(upload)

        if upload.is_image:
            generated = generate_image_presets(upload, storage)
            upload.metadata = {**upload.metadata, "presets": generated}

        upload.status = UploadStatus.COMPLETED
        upload.error_message = ""
    except FilePipelineError as exc:
        upload.status = UploadStatus.FAILED
        upload.error_message = str(exc)

    upload.save()
    return upload
