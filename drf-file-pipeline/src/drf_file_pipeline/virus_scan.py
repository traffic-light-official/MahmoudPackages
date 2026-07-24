"""A pluggable virus-scanning hook.

This package ships no actual scanning engine — wiring in ClamAV, a
cloud scanning API, or anything else is inherently deployment-specific.
:func:`null_scanner` is the documented default: it always reports a
file as clean, so the pipeline works out of the box, but it provides
**no actual protection**. Set ``FILE_PIPELINE["VIRUS_SCAN_CALLBACK"]``
to your own callable before relying on this in any environment that
accepts untrusted uploads — see ``docs/security.md``.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.utils.module_loading import import_string

from drf_file_pipeline.exceptions import VirusDetectedError
from drf_file_pipeline.models import FileUpload
from drf_file_pipeline.settings import get_setting


@dataclass(frozen=True, slots=True)
class ScanResult:
    """The outcome of scanning an upload.

    Attributes:
        clean: Whether the scanner considers the file safe.
        details: A human-readable explanation (empty when clean).
    """

    clean: bool
    details: str = ""


def null_scanner(upload: FileUpload) -> ScanResult:
    """The default virus-scan callback: always reports the file as clean.

    Args:
        upload: The upload being scanned. Unused — this scanner performs
            no actual inspection.

    Returns:
        Always ``ScanResult(clean=True)``.
    """
    del upload  # intentionally unused: this scanner performs no inspection
    return ScanResult(clean=True)


def scan_upload(upload: FileUpload) -> ScanResult:
    """Run the configured ``VIRUS_SCAN_CALLBACK`` against ``upload``.

    Raises:
        drf_file_pipeline.exceptions.VirusDetectedError: If the
            configured scanner reports the file as not clean.
    """
    callback = import_string(get_setting("VIRUS_SCAN_CALLBACK"))
    result: ScanResult = callback(upload)
    if not result.clean:
        raise VirusDetectedError(result.details or "The file was flagged by the virus scanner.")
    return result
