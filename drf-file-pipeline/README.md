# drf-file-pipeline

[![CI](https://github.com/mahmoudgshaker/drf-file-pipeline/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/mahmoudgshaker/drf-file-pipeline/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/drf-file-pipeline.svg)](https://pypi.org/project/drf-file-pipeline/)
[![Python versions](https://img.shields.io/pypi/pyversions/drf-file-pipeline.svg)](https://pypi.org/project/drf-file-pipeline/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Direct-to-S3 file uploads for Django REST Framework: your server issues
a presigned URL, the client uploads straight to S3, and your app never
proxies file bytes through a Django worker. Handles small single-part
uploads and large resumable multipart uploads through the same API,
with pluggable validation, virus scanning, and image-preset generation.

```python
POST /uploads/  {"filename": "report.pdf", "content_type": "application/pdf", "size": 2_400_000}
# -> {"upload": {...}, "presigned_post": {"url": "...", "fields": {...}}}

# client uploads directly to S3 using the returned URL/fields

POST /uploads/{id}/complete/
# -> {"status": "processing"}  # validation, virus scan, and (for images) preset generation run
```

## Why

Proxying uploads through your Django/DRF workers wastes worker time and
memory on bytes that are just going to end up in S3 anyway, and caps
your practical upload size at whatever your request timeout allows.
Presigned direct-to-S3 uploads remove Django from the data path
entirely — your server only ever issues short-lived, scoped credentials
and tracks upload state.

## Features

- **Presigned POST** for small uploads, **presigned multipart** for
  large/resumable ones — the same `InitiateUploadView` picks the right
  one based on size.
- **Resumable uploads**: `UploadPart` tracks completed parts, so a
  multipart upload can resume after a client disconnect without
  re-uploading finished parts.
- **Storage abstraction**: `StorageBackend` protocol, with
  `S3StorageBackend` built in — implement your own for GCS, Azure Blob,
  or MinIO.
- **Validation callbacks**: content-type and size checks out of the
  box, plus your own custom validators (`VALIDATION_CALLBACKS`), run
  before an upload is accepted and again before completion.
- **Pluggable virus scanning**: a documented no-op default, wire in
  ClamAV or a cloud scanning API via `VIRUS_SCAN_CALLBACK`.
- **Image presets and thumbnails**: configure named presets
  (dimensions, fit mode); generated automatically for image uploads via
  Pillow.
- **Background processing**: `process_upload()` is the single
  entry point for post-upload work (validation, scanning, image
  presets) — call it from whatever task queue you already run (Celery,
  RQ, a management-command loop).
- **Cleanup**: `cleanup_abandoned_uploads` management command removes
  uploads that never completed, past a configurable age.
- Fully typed, PEP 561 compatible, `mypy --strict` clean.

## Installation

```bash
pip install drf-file-pipeline
```

## Quick Start

```python
# settings.py
INSTALLED_APPS = [..., "drf_file_pipeline"]
FILE_PIPELINE = {
    "BUCKET_NAME": "my-uploads-bucket",
    "ALLOWED_CONTENT_TYPES": ["image/png", "image/jpeg", "application/pdf"],
    "MAX_UPLOAD_SIZE": 100 * 1024 * 1024,
    "IMAGE_PRESETS": {
        "thumbnail": {"width": 200, "height": 200, "mode": "cover"},
    },
}

# urls.py
from drf_file_pipeline.views import (
    AbortUploadView, CompleteUploadView, FileUploadViewSet, InitiateUploadView, PresignPartView,
)

# process a completed upload (call from your own task queue)
from drf_file_pipeline.processing import process_upload
process_upload(upload_id)
```

## Documentation

Full documentation: <https://mahmoudgshaker.github.io/drf-file-pipeline/>

- [Getting Started](docs/getting-started.md)
- [Installation](docs/installation.md)
- [Configuration](docs/configuration.md) / [Settings](docs/settings.md)
- [Quick Start](docs/quickstart.md)
- [Advanced Usage](docs/advanced-usage.md)
- [Architecture](docs/architecture.md)
- [API Reference](docs/api-reference.md)
- [Examples](docs/examples.md)
- [Common Patterns](docs/common-patterns.md)
- [Performance](docs/performance.md)
- [Security](docs/security.md)
- [Testing](docs/testing.md)
- [Deployment](docs/deployment.md)
- [FAQ](docs/faq.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Migration Guide](docs/migration.md)

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
