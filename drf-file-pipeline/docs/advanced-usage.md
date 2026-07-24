# Advanced Usage

## Writing a custom storage backend

`StorageBackend` is a `typing.Protocol` — implement its methods for GCS,
Azure Blob, MinIO, or any S3-compatible store that boto3 doesn't talk to
directly:

```python
from drf_file_pipeline.storage import StorageBackend, PresignedPost, ObjectInfo

class GCSStorageBackend:
    def create_presigned_post(self, *, key, content_type, max_size):
        ...  # build a GCS signed POST policy
    def create_multipart_upload(self, *, key, content_type): ...
    def presign_upload_part(self, *, key, upload_id, part_number): ...
    def complete_multipart_upload(self, *, key, upload_id, parts): ...
    def abort_multipart_upload(self, *, key, upload_id): ...
    def generate_presigned_get_url(self, *, key, expiry): ...
    def delete(self, *, key): ...
    def head(self, *, key): ...
    def download_to_path(self, *, key, path): ...
    def upload_from_path(self, *, key, path, content_type): ...
```

```python
FILE_PIPELINE = {"STORAGE_BACKEND": "myproject.storage.GCSStorageBackend"}
```

For an S3-compatible store with a different endpoint (MinIO,
Cloudflare R2, DigitalOcean Spaces), you often don't need a new backend
at all — subclass `S3StorageBackend` and pass an `endpoint_url` through
your own boto3 client:

```python
import boto3
from drf_file_pipeline.storage import S3StorageBackend

class MinIOStorageBackend(S3StorageBackend):
    def __init__(self):
        client = boto3.client("s3", endpoint_url="https://minio.internal:9000")
        super().__init__(client=client)
```

## Custom ownership / access control

`IsUploadOwner` implements one policy (anonymous-owned uploads are
open, authenticated-owned uploads are restricted to their owner). For a
different policy — e.g. requiring authentication for every upload, or
scoping by an API key instead of a Django user — write your own
permission class and swap it into the views:

```python
from rest_framework.permissions import BasePermission

class IsUploadOwnerOrStaff(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.owner_id == request.user.pk
```

```python
class MyInitiateUploadView(InitiateUploadView):
    permission_classes = [IsAuthenticated]
```

## Attaching an upload to your own model

`FileUpload` doesn't know about your domain models — attach it via your
own FK:

```python
class Document(models.Model):
    upload = models.OneToOneField("drf_file_pipeline.FileUpload", on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
```

Create the `Document` row once the upload reaches `COMPLETED` (e.g. in
your `process_upload_task`, after calling `process_upload()`).

## Running validation independent of the upload flow

`validate_upload()` and `scan_upload()` are plain functions — call them
outside the normal initiate/complete/process flow if you need to
re-validate an already-completed upload (a policy change, an audit):

```python
from drf_file_pipeline.validation import validate_upload
from drf_file_pipeline.virus_scan import scan_upload

for upload in FileUpload.objects.filter(status="completed"):
    try:
        validate_upload(upload)
        scan_upload(upload)
    except FilePipelineError as exc:
        flag_for_review(upload, exc)
```

## Generating presets outside `process_upload()`

`generate_image_presets()` is independently callable if you want preset
generation on a different trigger than the normal upload-completion flow
(e.g. regenerating presets after adding a new preset definition to
already-completed uploads):

```python
from drf_file_pipeline.images import generate_image_presets
from drf_file_pipeline.storage import get_storage_backend

storage = get_storage_backend()
for upload in FileUpload.objects.filter(status="completed"):
    if upload.is_image:
        generated = generate_image_presets(upload, storage)
        upload.metadata = {**upload.metadata, "presets": generated}
        upload.save(update_fields=["metadata"])
```
