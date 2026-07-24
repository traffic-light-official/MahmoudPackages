# Configuration

All configuration lives under a single Django setting, `FILE_PIPELINE`.
This page covers the decisions that matter most; see
[Settings](settings.md) for the exhaustive key-by-key reference.

## The bucket

```python
FILE_PIPELINE = {"BUCKET_NAME": "my-uploads-bucket"}
```

The only setting without a default. Everything else is optional.

## Choosing single-POST vs. multipart

```python
FILE_PIPELINE = {
    "BUCKET_NAME": "my-uploads-bucket",
    "MULTIPART_THRESHOLD": 25 * 1024 * 1024,   # bytes
    "MULTIPART_CHUNK_SIZE": 25 * 1024 * 1024,  # bytes, min 5 MiB (S3's own minimum)
}
```

`InitiateUploadView` compares the client's declared size against
`MULTIPART_THRESHOLD` to decide which upload mode to hand back. Lower
the threshold if you want more uploads to be resumable; raise
`MULTIPART_CHUNK_SIZE` to reduce the number of presigned part URLs
generated per large upload (fewer, larger parts).

## Validation

```python
FILE_PIPELINE = {
    "BUCKET_NAME": "my-uploads-bucket",
    "ALLOWED_CONTENT_TYPES": ["image/png", "image/jpeg", "application/pdf"],
    "MAX_UPLOAD_SIZE": 100 * 1024 * 1024,
    "VALIDATION_CALLBACKS": ["myproject.validators.check_pdf_page_count"],
}
```

Content-type and size checks run at initiate time (against what the
client *declares*) and again during `process_upload()` (against the
*actual* uploaded object) — the second pass is authoritative, since a
client's initiate-time claims can't be trusted. Custom callbacks in
`VALIDATION_CALLBACKS` run at both points too; write them to raise
`ValidationFailedError` on rejection:

```python
# myproject/validators.py
from drf_file_pipeline.exceptions import ValidationFailedError

def check_pdf_page_count(upload):
    if upload.content_type == "application/pdf" and get_page_count(upload) > 50:
        raise ValidationFailedError("PDFs over 50 pages are not accepted.")
```

## Virus scanning

```python
FILE_PIPELINE = {
    "BUCKET_NAME": "my-uploads-bucket",
    "VIRUS_SCAN_CALLBACK": "myproject.scanning.clamav_scan",
}
```

The default (`drf_file_pipeline.virus_scan.null_scanner`) always reports
clean — it provides **no actual protection**. See
[Security](security.md) before accepting untrusted uploads in
production.

## Image presets

```python
FILE_PIPELINE = {
    "BUCKET_NAME": "my-uploads-bucket",
    "IMAGE_PRESETS": {
        "thumbnail": {"width": 200, "height": 200, "mode": "cover"},
        "preview": {"width": 800, "height": 800, "mode": "contain"},
    },
}
```

Generated automatically during `process_upload()` for any upload whose
content type starts with `IMAGE_CONTENT_TYPE_PREFIX` (default
`"image/"`). Each preset's storage key and mode are recorded in
`upload.metadata["presets"]`.

## Cleanup age

```python
FILE_PIPELINE = {"BUCKET_NAME": "my-uploads-bucket", "ABANDONED_UPLOAD_MAX_AGE_HOURS": 24}
```

Controls the default age threshold for `cleanup_abandoned_uploads`
(overridable per-run with `--max-age-hours`).
