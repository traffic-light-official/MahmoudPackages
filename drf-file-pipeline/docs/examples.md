# Examples

Runnable/adaptable snippets live in [`examples/`](https://github.com/mahmoudgshaker/drf-file-pipeline/tree/main/examples)
in the repository. This page walks through the same scenarios inline.

## A custom validator

```python
# examples/custom_validator.py
from drf_file_pipeline.exceptions import ValidationFailedError
from drf_file_pipeline.models import FileUpload

def reject_executables(upload: FileUpload) -> None:
    if upload.original_filename.lower().endswith((".exe", ".bat", ".sh", ".dll")):
        raise ValidationFailedError(f"Executable files are not accepted: {upload.original_filename!r}.")
```

```python
FILE_PIPELINE = {
    "BUCKET_NAME": "my-uploads-bucket",
    "VALIDATION_CALLBACKS": ["examples.custom_validator.reject_executables"],
}
```

## A ClamAV virus scanner

```python
# examples/clamav_scanner.py
import clamd  # pip install clamd; not a dependency of this package

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
```

```python
FILE_PIPELINE = {
    "BUCKET_NAME": "my-uploads-bucket",
    "VIRUS_SCAN_CALLBACK": "examples.clamav_scanner.clamav_scan",
}
```

## Wiring `process_upload()` into Celery

```python
# examples/tasks.py
from celery import shared_task
from drf_file_pipeline.processing import process_upload

@shared_task(bind=True, max_retries=3)
def process_upload_task(self, upload_id: str) -> None:
    try:
        process_upload(upload_id)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30) from exc
```

## A custom S3-compatible backend (MinIO)

```python
# examples/minio_storage.py
import boto3
from drf_file_pipeline.storage import S3StorageBackend

class MinIOStorageBackend(S3StorageBackend):
    def __init__(self) -> None:
        client = boto3.client(
            "s3",
            endpoint_url="https://minio.internal:9000",
            aws_access_key_id="minioadmin",
            aws_secret_access_key="minioadmin",
        )
        super().__init__(client=client)
```

## Attaching an upload to your own model

```python
# examples/attach_to_model.py
from django.db import models

class Document(models.Model):
    upload = models.OneToOneField(
        "drf_file_pipeline.FileUpload", on_delete=models.CASCADE, related_name="document"
    )
    title = models.CharField(max_length=200)
```

## Full lifecycle via the Python API (no HTTP)

```python
# examples/programmatic_upload.py
from drf_file_pipeline.models import FileUpload, UploadStatus
from drf_file_pipeline.processing import process_upload
from drf_file_pipeline.storage import get_storage_backend

def upload_file_directly(local_path: str, content_type: str) -> FileUpload:
    """Upload a local file without going through the presigned-URL HTTP flow —
    useful for data migrations or admin tooling where the file is already
    on the server, not a browser client."""
    storage = get_storage_backend()
    key = f"uploads/direct/{local_path.rsplit('/', 1)[-1]}"
    storage.upload_from_path(key=key, path=local_path, content_type=content_type)

    upload = FileUpload.objects.create(
        key=key,
        original_filename=local_path.rsplit("/", 1)[-1],
        content_type=content_type,
        status=UploadStatus.UPLOADED,
    )
    return process_upload(upload.pk)
```

See [Common Patterns](common-patterns.md) for more real-world recipes.
