"""Full lifecycle via the Python API, with no HTTP request involved.

See ``docs/examples.md``. Useful for data migrations or admin tooling
where the file is already on the server, not arriving from a browser
client.
"""

from __future__ import annotations

from drf_file_pipeline.models import FileUpload, UploadStatus
from drf_file_pipeline.processing import process_upload
from drf_file_pipeline.storage import get_storage_backend


def upload_file_directly(local_path: str, content_type: str) -> FileUpload:
    storage = get_storage_backend()
    filename = local_path.rsplit("/", 1)[-1]
    key = f"uploads/direct/{filename}"
    storage.upload_from_path(key=key, path=local_path, content_type=content_type)

    upload = FileUpload.objects.create(
        key=key,
        original_filename=filename,
        content_type=content_type,
        status=UploadStatus.UPLOADED,
    )
    return process_upload(upload.pk)
