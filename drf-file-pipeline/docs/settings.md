# Settings Reference

Every key recognized in the `FILE_PIPELINE` Django setting.

```python
FILE_PIPELINE = {
    "STORAGE_BACKEND": "drf_file_pipeline.storage.S3StorageBackend",
    "BUCKET_NAME": None,
    "AWS_REGION": None,
    "KEY_PREFIX": "uploads/",
    "PRESIGNED_UPLOAD_EXPIRY": 3600,
    "PRESIGNED_DOWNLOAD_EXPIRY": 300,
    "MULTIPART_THRESHOLD": 25 * 1024 * 1024,
    "MULTIPART_CHUNK_SIZE": 25 * 1024 * 1024,
    "MAX_UPLOAD_SIZE": None,
    "ALLOWED_CONTENT_TYPES": None,
    "VALIDATION_CALLBACKS": (),
    "VIRUS_SCAN_CALLBACK": "drf_file_pipeline.virus_scan.null_scanner",
    "IMAGE_PRESETS": {},
    "IMAGE_CONTENT_TYPE_PREFIX": "image/",
    "ABANDONED_UPLOAD_MAX_AGE_HOURS": 24,
}
```

| Key | Default | Description |
|---|---|---|
| `STORAGE_BACKEND` | `"drf_file_pipeline.storage.S3StorageBackend"` | Dotted path to a `StorageBackend` implementation. |
| `BUCKET_NAME` | `None` | S3 bucket name. Required to use `S3StorageBackend`. |
| `AWS_REGION` | `None` | AWS region for the S3 client. `None` defers to boto3's own region resolution. |
| `KEY_PREFIX` | `"uploads/"` | Prefix applied to every object key this package generates. |
| `PRESIGNED_UPLOAD_EXPIRY` | `3600` | Seconds a presigned upload URL (POST or multipart part) remains valid. |
| `PRESIGNED_DOWNLOAD_EXPIRY` | `300` | Seconds a presigned download URL (`FileUploadSerializer.download_url`) remains valid. |
| `MULTIPART_THRESHOLD` | `26214400` (25 MiB) | Uploads at or above this size use multipart instead of a single presigned POST. |
| `MULTIPART_CHUNK_SIZE` | `26214400` (25 MiB) | Size of each multipart part except the last. Must be at least 5 MiB (S3's own minimum). |
| `MAX_UPLOAD_SIZE` | `None` | Hard cap on any single upload, in bytes. `None` disables the check. |
| `ALLOWED_CONTENT_TYPES` | `None` | Allowed MIME types. `None` disables the check. |
| `VALIDATION_CALLBACKS` | `()` | Dotted paths to `(upload) -> None` callables; each raises `ValidationFailedError` to reject. |
| `VIRUS_SCAN_CALLBACK` | `"drf_file_pipeline.virus_scan.null_scanner"` | Dotted path to a `(upload) -> ScanResult` callable. |
| `IMAGE_PRESETS` | `{}` | `{name: {"width", "height", "mode"}}` — presets generated for image uploads. |
| `IMAGE_CONTENT_TYPE_PREFIX` | `"image/"` | MIME prefix used to decide whether an upload is eligible for preset generation. |
| `ABANDONED_UPLOAD_MAX_AGE_HOURS` | `24` | Default age threshold for `cleanup_abandoned_uploads`. |

## Validation

Every key is validated when first accessed (and re-validated after any
`FILE_PIPELINE` change, including in `@override_settings` blocks in
tests):

- Unknown keys raise `ImproperlyConfigured`, listing the valid ones.
- Wrong value types raise `ImproperlyConfigured`, naming the expected type.
- A `MULTIPART_CHUNK_SIZE` below 5 MiB raises `ImproperlyConfigured`
  explicitly (S3 rejects smaller non-final parts, so this fails fast at
  configuration time instead of on the first large upload).

## Runtime access

```python
from drf_file_pipeline.settings import get_setting

get_setting("MULTIPART_THRESHOLD")
```

Raises `KeyError` for an unrecognized key name.
