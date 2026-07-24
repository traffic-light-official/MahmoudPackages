"""Direct-to-S3 upload pipeline for Django REST Framework.

Presigned uploads (single-request POST for small files, resumable
multipart for large ones) keep file bytes off your Django workers
entirely. Validation, virus scanning, and image-preset generation run
in :func:`~drf_file_pipeline.processing.process_upload`, which you call
from whatever background task queue you already run.

Typical usage::

    # settings.py
    INSTALLED_APPS = [..., "drf_file_pipeline"]
    FILE_PIPELINE = {"BUCKET_NAME": "my-uploads-bucket"}

    # urls.py
    from drf_file_pipeline.views import InitiateUploadView, CompleteUploadView

    # tasks.py
    from drf_file_pipeline.processing import process_upload
"""

from __future__ import annotations

from drf_file_pipeline.exceptions import (
    FilePipelineError,
    InvalidUploadStateError,
    StorageError,
    ValidationFailedError,
    VirusDetectedError,
)

__version__ = "1.0.0"

__all__ = [
    "FilePipelineError",
    "InvalidUploadStateError",
    "StorageError",
    "ValidationFailedError",
    "VirusDetectedError",
    "__version__",
]
