# Quick Start

The full lifecycle, small and large uploads, resumability, and
processing — end to end.

## 1. Set up

```python
# settings.py
INSTALLED_APPS = [..., "drf_file_pipeline"]
FILE_PIPELINE = {
    "BUCKET_NAME": "my-uploads-bucket",
    "MULTIPART_THRESHOLD": 10 * 1024 * 1024,
    "IMAGE_PRESETS": {"thumbnail": {"width": 200, "height": 200, "mode": "cover"}},
}
```

```bash
python manage.py migrate drf_file_pipeline
```

## 2. Small file: presigned POST

```
POST /uploads/initiate/
{"filename": "avatar.png", "content_type": "image/png", "size": 50000}

-> 201
{"upload": {"id": "U1", "status": "uploading"}, "presigned_post": {"url": "...", "fields": {...}}}
```

Client POSTs the file to `presigned_post.url` with `presigned_post.fields`
as form data (standard S3 presigned-POST form upload), then:

```
POST /uploads/U1/complete/
-> 200 {"status": "uploaded"}
```

## 3. Large file: presigned multipart, with resume

```
POST /uploads/initiate/
{"filename": "video.mp4", "content_type": "video/mp4", "size": 104857600}

-> 201
{
  "upload": {"id": "U2", "status": "uploading"},
  "multipart": {"upload_id": "...", "chunk_size": 10485760, "parts": [{"part_number": 1, "url": "..."}, ...]}
}
```

Client uploads each part directly to its presigned URL, then reports
each completed part's ETag:

```
POST /uploads/U2/parts/
{"part_number": 1, "etag": "\"abc123\"", "size": 10485760}
-> 201
```

If a presigned part URL expires before the client gets to it (a slow
connection, a long pause), re-presign just that part:

```
GET /uploads/U2/parts/3/presign/
-> 200 {"part_number": 3, "url": "..."}
```

Check `GET /uploads/U2/` any time to see which parts are already
recorded (`parts` in the response) before deciding what's left to
upload. Once every part is done:

```
POST /uploads/U2/complete/
-> 200 {"status": "uploaded"}
```

## 4. Process both

```python
# tasks.py
from celery import shared_task
from drf_file_pipeline.processing import process_upload

@shared_task
def process_upload_task(upload_id):
    process_upload(upload_id)
```

Trigger it after `complete/` succeeds (in the view, a signal, or however
fits your app). For `U1` (the PNG), this generates the configured
`thumbnail` preset; for `U2` (the video, not an image), it just runs
validation and virus scanning.

```
GET /uploads/U1/
-> {"status": "completed", "metadata": {"presets": {"thumbnail": "uploads/.../avatar__thumbnail.png"}}, "download_url": "..."}
```

## 5. Clean up abandoned uploads

```bash
python manage.py cleanup_abandoned_uploads --dry-run   # see what would go
python manage.py cleanup_abandoned_uploads              # actually delete
```

Run this on a schedule (cron, Celery beat) — see
[Deployment](deployment.md).

See [Common Patterns](common-patterns.md) for real-world variations
(ownership models, custom validators, non-S3 backends).
