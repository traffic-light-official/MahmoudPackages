# Migration Guide

## Adding this package to an existing project

`drf_file_pipeline` ships its own tables (`FileUpload`, `UploadPart`) —
adding it to `INSTALLED_APPS` and running its migration doesn't touch
any of your existing models or data:

```python
INSTALLED_APPS = [..., "drf_file_pipeline"]
FILE_PIPELINE = {"BUCKET_NAME": "my-uploads-bucket"}
```

```bash
python manage.py migrate drf_file_pipeline
```

There's nothing to reconcile — this is purely additive.

## Migrating from a server-proxied upload endpoint

If you currently accept uploads by receiving the file bytes directly
(a `FileField`/`ImageField` on a `ModelSerializer`, or a raw
`request.FILES` handler), moving to presigned direct-to-S3 uploads is a
client-visible API change, not a drop-in replacement — the request
shape is fundamentally different (JSON describing the file, not
multipart form data containing it). Plan for:

1. **A transition period** where both endpoints exist, if you can't
   deploy client and server changes atomically. Keep the old endpoint
   working while the new one is adopted; retire it once every client is
   migrated.
2. **Client changes**: the client now makes two (or more, for
   multipart) requests instead of one — initiate, upload directly to
   S3, then report completion. This is unavoidable with presigned
   uploads; there's no way to preserve a single-request client contract
   while also getting bytes off your server.
3. **Attaching the upload to your existing models**: see
   [Advanced Usage](advanced-usage.md#attaching-an-upload-to-your-own-model)
   — typically a nullable FK from your existing model to `FileUpload`,
   backfilled as uploads migrate to the new flow, with the old
   `FileField` column dropped once nothing references it.

## Migrating existing files already in S3 (or elsewhere) into this package's tracking

If you already store files in S3 but without `FileUpload` rows tracking
them (e.g. you used `django-storages`' `FileField` directly), backfill
one `FileUpload` per existing object with a data migration or one-off
script:

```python
from drf_file_pipeline.models import FileUpload, UploadStatus
from drf_file_pipeline.storage import get_storage_backend

def backfill_file_upload(existing_key: str, original_filename: str, content_type: str) -> FileUpload:
    storage = get_storage_backend()
    info = storage.head(key=existing_key)
    return FileUpload.objects.create(
        key=existing_key,
        original_filename=original_filename,
        content_type=content_type,
        size=info.size if info else None,
        status=UploadStatus.COMPLETED,
    )
```

Note `FileUpload.key` has a unique constraint — this only works
one-to-one; if multiple existing records currently point at the same S3
object, you'll need to decide how to represent that (this package
assumes one `FileUpload` row per object).

## Migrating from another upload-tracking package

There's no automatic converter — the general approach is the same as
above: for each existing record, create a `FileUpload` row with
`status=COMPLETED` pointing at the file's existing S3 key (assuming it
stays in S3; if it's in a different store, copy it first, or implement
a custom `StorageBackend` matching its current location — see
[Advanced Usage](advanced-usage.md#writing-a-custom-storage-backend)).
Once migrated, existing image thumbnails from the old system won't
automatically populate `metadata["presets"]` — regenerate them via
[Advanced Usage](advanced-usage.md#generating-presets-outside-process_upload)
if you want that populated for pre-existing uploads too.

## Version compatibility

This package follows [Semantic Versioning](https://semver.org/). A
major version bump may include a schema migration — always run
`python manage.py migrate drf_file_pipeline` after upgrading, and check
[CHANGELOG.md](https://github.com/mahmoudgshaker/drf-file-pipeline/blob/main/CHANGELOG.md)
for any breaking changes to `StorageBackend`'s protocol (a custom
backend may need updating to match).
