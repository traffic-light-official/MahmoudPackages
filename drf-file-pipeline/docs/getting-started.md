# Getting Started

## Install

```bash
pip install drf-file-pipeline
```

Requires an S3 bucket and AWS credentials boto3 can discover (an IAM
role, environment variables, or a shared credentials file) — the
built-in `S3StorageBackend` doesn't accept credentials directly; it
relies on boto3's normal credential resolution.

## 1. Add the app and configure the bucket

```python
# settings.py
INSTALLED_APPS = [..., "drf_file_pipeline"]
FILE_PIPELINE = {
    "BUCKET_NAME": "my-uploads-bucket",
}
```

Run migrations — this package ships one, for the `FileUpload`/`UploadPart`
models that track lifecycle state:

```bash
python manage.py migrate drf_file_pipeline
```

## 2. Wire up the views

```python
# urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter
from drf_file_pipeline.views import (
    AbortUploadView, CompleteUploadView, FileUploadViewSet, InitiateUploadView,
    PresignPartView, ReportPartView,
)

router = DefaultRouter()
router.register("uploads", FileUploadViewSet, basename="fileupload")

urlpatterns = [
    path("uploads/initiate/", InitiateUploadView.as_view()),
    path("uploads/<uuid:pk>/parts/", ReportPartView.as_view()),
    path("uploads/<uuid:pk>/parts/<int:part_number>/presign/", PresignPartView.as_view()),
    path("uploads/<uuid:pk>/complete/", CompleteUploadView.as_view()),
    path("uploads/<uuid:pk>/abort/", AbortUploadView.as_view()),
    *router.urls,
]
```

## 3. Your first upload

```
POST /uploads/initiate/
{"filename": "report.pdf", "content_type": "application/pdf", "size": 2400000}

-> 201
{
  "upload": {"id": "...", "status": "uploading", ...},
  "presigned_post": {"url": "https://my-uploads-bucket.s3.amazonaws.com/", "fields": {...}}
}
```

The client then POSTs the file directly to `presigned_post.url` using
`presigned_post.fields` as form fields (standard S3 presigned-POST
usage), then tells your server it's done:

```
POST /uploads/{id}/complete/
-> 200 {"status": "uploaded", ...}
```

## 4. Process it

Validation, virus scanning, and image presets run in
`process_upload()` — call it from your own background task queue after
`complete/` succeeds:

```python
# tasks.py (Celery example)
from celery import shared_task
from drf_file_pipeline.processing import process_upload

@shared_task
def process_upload_task(upload_id):
    process_upload(upload_id)
```

```python
# views.py, after marking the upload uploaded:
process_upload_task.delay(str(upload.pk))
```

## Next steps

- [Quick Start](quickstart.md) for the full multipart/resumable flow.
- [Configuration](configuration.md) for validation, scanning, and image
  preset options.
- [Testing](testing.md) for testing against a mocked S3 in your own
  suite.
