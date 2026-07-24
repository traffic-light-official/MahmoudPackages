# Common Patterns

## Requiring authentication to upload

The default `InitiateUploadView.permission_classes = [AllowAny]`
supports anonymous upload flows. To require authentication project-wide:

```python
from rest_framework.permissions import IsAuthenticated
from drf_file_pipeline.views import InitiateUploadView

class MyInitiateUploadView(InitiateUploadView):
    permission_classes = [IsAuthenticated]
```

## Per-user upload quotas

Check the user's existing storage usage in a custom validator before
the upload is even initiated (validators run at initiate time too):

```python
def enforce_user_quota(upload):
    if upload.owner_id is None:
        return
    used = FileUpload.objects.filter(owner_id=upload.owner_id, status="completed").aggregate(
        total=Sum("size")
    )["total"] or 0
    if used + (upload.size or 0) > USER_QUOTA_BYTES:
        raise ValidationFailedError("Storage quota exceeded.")
```

## Rejecting uploads by filename pattern

```python
import re
from drf_file_pipeline.exceptions import ValidationFailedError

_BLOCKED = re.compile(r"\.(exe|bat|scr|dll)$", re.IGNORECASE)

def reject_by_extension(upload):
    if _BLOCKED.search(upload.original_filename):
        raise ValidationFailedError("This file type is not accepted.")
```

## Notifying on completion

Hook into `process_upload()`'s result rather than the HTTP `complete/`
response — the upload isn't really done (validated, scanned, presets
generated) until processing finishes:

```python
@shared_task
def process_upload_task(upload_id):
    upload = process_upload(upload_id)
    if upload.status == "completed":
        notify_owner.delay(upload.pk)
    elif upload.status == "failed":
        notify_owner_of_failure.delay(upload.pk, upload.error_message)
```

## Serving downloads through your CDN instead of S3 directly

`FileUploadSerializer.download_url` always calls
`storage.generate_presigned_get_url()`. Override it in your own
serializer if you front S3 with CloudFront or another CDN:

```python
class CDNFileUploadSerializer(FileUploadSerializer):
    def get_download_url(self, obj):
        if obj.status != "completed":
            return None
        return f"https://cdn.example.com/{obj.key}"
```

## Generating presets for already-completed uploads

After adding a new preset to `IMAGE_PRESETS`, backfill it for existing
uploads with a one-off script (see
[Advanced Usage](advanced-usage.md#generating-presets-outside-process_upload)).

## Restricting cleanup to specific content types

`cleanup_abandoned_uploads` doesn't filter by content type — if you only
want to auto-clean certain kinds of abandoned uploads (e.g. large video
uploads that are expensive to leave dangling, but keep small pending
uploads around longer for manual review), write your own management
command reusing the building blocks:

```python
from drf_file_pipeline.models import FileUpload, UploadStatus
from drf_file_pipeline.storage import get_storage_backend

def cleanup_abandoned_videos(max_age_hours=6):
    storage = get_storage_backend()
    cutoff = timezone.now() - timedelta(hours=max_age_hours)
    stale = FileUpload.objects.filter(
        status__in=[UploadStatus.PENDING, UploadStatus.UPLOADING],
        content_type__startswith="video/",
        created_at__lt=cutoff,
    )
    for upload in stale:
        if upload.is_multipart:
            storage.abort_multipart_upload(key=upload.key, upload_id=upload.upload_id)
    stale.delete()
```
