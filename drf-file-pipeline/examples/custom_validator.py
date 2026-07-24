"""A custom validation callback. See ``docs/examples.md``."""

from __future__ import annotations

from drf_file_pipeline.exceptions import ValidationFailedError
from drf_file_pipeline.models import FileUpload


def reject_executables(upload: FileUpload) -> None:
    if upload.original_filename.lower().endswith((".exe", ".bat", ".sh", ".dll")):
        raise ValidationFailedError(
            f"Executable files are not accepted: {upload.original_filename!r}."
        )
