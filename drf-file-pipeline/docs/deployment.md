# Deployment

## S3 bucket setup

- Enable versioning if you want protection against accidental deletes
  (this package's `cleanup_abandoned_uploads` deletes objects
  permanently otherwise).
- Configure a lifecycle rule to abort incomplete multipart uploads
  after N days as a backstop — `cleanup_abandoned_uploads` handles this
  at the application level, but an S3-level lifecycle rule protects
  against storage costs from uploads this package never learns about
  (e.g. a client that called `create_multipart_upload` via a leaked
  presigned flow outside your API, or a `FileUpload` row lost to a
  database issue).
- CORS configuration is required for browser clients to POST/PUT
  directly to presigned URLs — allow your frontend's origin(s) with
  `PUT`/`POST` methods and the headers this package's presigned
  requests use (`Content-Type` at minimum).

## Running `process_upload()` in the background

This package ships no worker — wire `process_upload()` into whatever
you run:

```python
# Celery
@shared_task
def process_upload_task(upload_id):
    process_upload(upload_id)

# Trigger after CompleteUploadView succeeds, e.g. via a signal or directly
# in a customized view.
```

For a simpler deployment with no task queue, poll for uploaded-but-unprocessed
rows from a scheduled job:

```python
# management/commands/process_pending_uploads.py
from django.core.management.base import BaseCommand
from drf_file_pipeline.models import FileUpload, UploadStatus
from drf_file_pipeline.processing import process_upload

class Command(BaseCommand):
    def handle(self, *args, **options):
        for upload in FileUpload.objects.filter(status=UploadStatus.UPLOADED):
            process_upload(upload.pk)
```

## Scheduling cleanup

Run `cleanup_abandoned_uploads` on a schedule — a cron job, Celery beat,
or a Kubernetes CronJob:

```
# crontab
0 * * * * cd /app && python manage.py cleanup_abandoned_uploads
```

```python
# celery beat schedule
CELERY_BEAT_SCHEDULE = {
    "cleanup-abandoned-uploads": {
        "task": "myproject.tasks.cleanup_abandoned_uploads_task",
        "schedule": crontab(minute=0),  # hourly
    },
}
```

## Migrations

`drf_file_pipeline` ships one migration (`0001_initial`) for its
`FileUpload`/`UploadPart` models — run it like any other app's:

```bash
python manage.py migrate drf_file_pipeline
```

## Zero-downtime rollout of a new `FILE_PIPELINE` setting

`FILE_PIPELINE` settings are read on every access (with process-local
caching invalidated via Django's `setting_changed` signal, which mainly
matters for tests) — a rolling deploy that changes `FILE_PIPELINE` takes
effect as each worker process restarts with the new settings, with no
migration or manual cache-clear step needed.

## Monitoring

- Track `process_upload()` failures (`upload.status == "failed"`,
  `upload.error_message`) — a spike often means a validation rule or
  scanner is misconfigured, not that uploads themselves are actually
  failing.
- Alert on `cleanup_abandoned_uploads` consistently deleting a large
  number of uploads — that usually means clients are failing to reach
  `complete/`, not that cleanup itself is misbehaving.
