# drf-file-pipeline

Direct-to-S3 file uploads for Django REST Framework.

Your server issues a presigned URL (or, for large files, a presigned
multipart upload); the client uploads straight to S3; your Django
workers never see the file's bytes. Validation, virus scanning, and
image-preset generation run afterward, in a single background-processing
entry point you call from whatever task queue you already run.

## Why direct-to-S3

Proxying uploads through your application server costs worker time and
memory on bytes that are just going to end up in object storage anyway,
and caps your practical upload size at whatever your request timeout
allows. Presigned uploads remove the application server from the data
path entirely.

## What it does

- Presigned POST for small files, presigned multipart for large or
  resumable ones, through one `InitiateUploadView`.
- Tracks upload state (`FileUpload`) and completed multipart parts
  (`UploadPart`) so a resumed upload can skip parts already done.
- Validates content-type/size (and your own custom rules) both at
  initiate time and again, authoritatively, during processing.
- Runs a pluggable virus-scan hook before marking an upload complete.
- Generates named image presets/thumbnails via Pillow.
- Exposes `process_upload()` as the one function you wire into your own
  background task queue — no worker of its own.
- Cleans up abandoned uploads via a management command.

## Where to go next

- New to the package? Start with [Getting Started](getting-started.md).
- Migrating an existing Django project onto this? See the
  [Migration Guide](migration.md).
- Want to understand the upload lifecycle and why validation runs
  twice? See [Architecture](architecture.md).
- Looking for a specific class or function? See
  [API Reference](api-reference.md).
