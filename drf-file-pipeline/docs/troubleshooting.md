# Troubleshooting

## `ImproperlyConfigured: FILE_PIPELINE['BUCKET_NAME'] must be set`

`S3StorageBackend` was constructed without `BUCKET_NAME` configured
(and none passed explicitly). Set `FILE_PIPELINE = {"BUCKET_NAME": "..."}`
in settings.

## 403 Forbidden when the client tries to use a presigned POST/URL

Usually one of:

- The IAM identity boto3 is using lacks the required S3 permissions
  (see [Installation](installation.md#aws-credentials-and-permissions)).
- The presigned URL expired (`PRESIGNED_UPLOAD_EXPIRY`/`PRESIGNED_DOWNLOAD_EXPIRY`)
  — for a stalled multipart part, re-presign it via `PresignPartView`
  rather than reusing the original.
- CORS isn't configured on the bucket for a browser client (see
  [Deployment](deployment.md#s3-bucket-setup)).

## `409 Conflict` from `CompleteUploadView`/`AbortUploadView`

These enforce the upload's current status: `complete/` requires
`UPLOADING`; `abort/` requires `PENDING` or `UPLOADING`. A 409 means the
upload has already moved on (completed, aborted, or is being
processed) — check `GET /uploads/{id}/` for its current `status`.

## `409 Conflict` from `PresignPartView`

The upload isn't a multipart upload (`upload.upload_id` is `None`) —
this endpoint only applies to uploads that went through the multipart
path (declared size at or above `MULTIPART_THRESHOLD`).

## `process_upload()` marks everything as `FAILED` with "not found"

`storage.head()` didn't find the object at `upload.key` — the client
either never actually uploaded the bytes, uploaded to a different key,
or (for multipart) never called `complete/` (which is what triggers S3
to assemble the parts into the final object — without it, the object
doesn't exist yet even if every part was uploaded).

## Presets aren't generated even though `IMAGE_PRESETS` is set

Check `upload.content_type` actually starts with
`IMAGE_CONTENT_TYPE_PREFIX` — a client that declares
`application/octet-stream` for an actual PNG won't be treated as an
image. Consider adding a custom validator that cross-checks declared
content-type against the real file (e.g. via `python-magic`) if this
matters for your application.

## A generated preset is the wrong format (e.g. saved as PNG instead of JPEG)

This was a real bug in earlier development, fixed by capturing the
source image's format *before* calling `ImageOps.exif_transpose()` (see
[Architecture](architecture.md#a-real-bug-this-design-caught-image-format-detection)).
If you see this with the current version, it likely means the *source*
object in storage genuinely isn't the format its `content_type` claims —
Pillow saves using the format it detected from the actual file bytes,
not from `upload.content_type`.

## `moto`-based tests fail with a real AWS 403/network error

A test is hitting real AWS instead of the mock — usually because it
doesn't request the fixture that activates `mock_aws()` (see
[Testing](testing.md)). Every test exercising `get_storage_backend()`
or any `StorageBackend` method needs the mocking context active for its
entire duration.

## `MULTIPART_CHUNK_SIZE` raises `ImproperlyConfigured` at import time

It must be at least 5 MiB — S3 rejects smaller non-final multipart
parts. This is validated eagerly so misconfiguration fails at startup,
not on the first large upload in production.

## Still stuck?

Open a [GitHub Discussion](https://github.com/mahmoudgshaker/drf-file-pipeline/discussions)
with your `FILE_PIPELINE` settings (redact anything sensitive) and the
upload's current `status`/`error_message`.
