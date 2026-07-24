"""A ClamAV-backed virus-scan callback. See ``docs/examples.md``.

Requires ``pip install clamd`` — not a dependency of this package (the
built-in default, ``null_scanner``, performs no scanning at all; wiring
in a real scanner is inherently deployment-specific).
"""

from __future__ import annotations

import clamd

from drf_file_pipeline.models import FileUpload
from drf_file_pipeline.storage import get_storage_backend
from drf_file_pipeline.virus_scan import ScanResult


def clamav_scan(upload: FileUpload) -> ScanResult:
    storage = get_storage_backend()
    client = clamd.ClamdNetworkSocket(host="clamav.internal", port=3310)
    local_path = f"/tmp/scan-{upload.pk}"
    storage.download_to_path(key=upload.key, path=local_path)
    result = client.scan(local_path)
    status, _details = result[local_path]
    return ScanResult(clean=(status == "OK"), details=str(result))
