# Security

File upload endpoints are a classic attack surface. Here's exactly what
this package does and does not protect against.

## Virus scanning is opt-in, not automatic

The default `VIRUS_SCAN_CALLBACK` (`null_scanner`) always reports a file
as clean — **it performs no actual scanning**. If your application
accepts uploads from untrusted users, wire in a real scanner (ClamAV, a
cloud scanning API) via `VIRUS_SCAN_CALLBACK` before going to production
— see [Configuration](configuration.md) and
[Examples](examples.md#a-clamav-virus-scanner). This is a deliberate
default (this package ships no scanning engine of its own — see
[Architecture](architecture.md)), not an oversight, but it means the
out-of-the-box behavior accepts everything.

## Client-declared metadata is never trusted for authorization decisions

The content-type and size a client declares at `initiate/` time can be
anything — presigned uploads mean Django never inspects the bytes in
transit. `process_upload()` re-validates against the *actual* object in
storage (`storage.head()`'s real size) before marking anything
`COMPLETED`. Never make an authorization or business-logic decision
based on `FileUpload.content_type`/`.size` before `process_upload()` has
run — they may not yet reflect reality.

## Presigned URLs are scoped and short-lived, not indefinite access

- Upload URLs expire after `PRESIGNED_UPLOAD_EXPIRY` (default 1 hour).
- Download URLs expire after `PRESIGNED_DOWNLOAD_EXPIRY` (default 5
  minutes) and are only issued for `COMPLETED` uploads
  (`FileUploadSerializer.download_url` returns `None` otherwise).
- Presigned POST conditions include a `content-length-range` when
  `MAX_UPLOAD_SIZE` is configured — S3 itself enforces the size cap at
  upload time, not just at your API layer.

Configure `MAX_UPLOAD_SIZE` if you accept uploads from untrusted clients
— without it, a presigned POST places no upper bound on what a client
can actually upload to your bucket.

## Object keys are generated server-side, never from client input directly

`build_object_key()` generates every storage key as
`{KEY_PREFIX}{uuid4()}/{sanitized_filename}` — the client-supplied
filename is stripped to `[A-Za-z0-9._-]` before being used in the key,
and the UUID prefix means no client input ever determines *which*
object gets written or overwritten. This rules out path traversal
(`../../etc/passwd`-style filenames) and key-collision attacks (a
client can't force an overwrite of another upload's object).

## IAM least privilege

Grant only the actions this package actually uses — see
[Installation](installation.md#aws-credentials-and-permissions).
Broader S3 permissions (bucket-wide delete, `s3:*`) are unnecessary and
increase blast radius if credentials leak.

## Image processing and decompression bombs

`generate_image_presets()` uses Pillow, which — like any image
library — can be a resource-exhaustion vector against maliciously
crafted images (extremely large dimensions, decompression bombs).
Pillow's own `Image.MAX_IMAGE_PIXELS` guard (enabled by default) raises
a `DecompressionBombError` for images with an unreasonable pixel count;
don't disable it. If you accept images from fully untrusted sources,
also consider a resource/time limit around `process_upload()` itself
(a Celery task timeout, for instance).

## The anonymous-owner model has real access implications

Uploads with `owner=None` are accessible to anyone who knows the
upload's id — there is no secondary secret involved (see
[Architecture](architecture.md#why-the-manager-isnt-a-tenantmanager-style-auto-scoper)).
`FileUpload.id` is a UUID4 (not sequential, not guessable), which makes
this a reasonable "possession of the id is authorization" model for
many use cases — but it is not equivalent to authentication. Require
`IsAuthenticated` (see [Common Patterns](common-patterns.md#requiring-authentication-to-upload))
if anonymous access to any upload by id is not acceptable for your
application.

## Reporting a vulnerability

See [SECURITY.md](https://github.com/mahmoudgshaker/drf-file-pipeline/blob/main/SECURITY.md)
in the repository root for the disclosure process.
