# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-07-24

### Added

- Initial release.
- `FileUpload` / `UploadPart` models tracking upload lifecycle, with a
  real migration.
- Direct-to-S3 uploads via presigned POST (small files) and presigned
  multipart uploads (large/resumable files), through a pluggable
  `StorageBackend` abstraction (`S3StorageBackend` built in).
- `InitiateUploadView`, `PresignPartView`, `CompleteUploadView`,
  `AbortUploadView`, and `FileUploadViewSet` (read-only status/list).
- Validation callbacks (content-type, size, custom) run before an
  upload is accepted and again before it's marked complete.
- Pluggable virus-scanning hook (`VIRUS_SCAN_CALLBACK`), with a
  documented no-op default.
- Image presets and thumbnail generation via Pillow, with derived S3
  keys per preset.
- `process_upload()` — the single background-processing entry point,
  designed to be called from your own task queue (Celery, RQ, or a
  management-command loop).
- `cleanup_abandoned_uploads` management command for uploads stuck
  before completion past a configurable age.
- `IsUploadOwner` permission.
- Full test suite (S3 mocked via `moto`) across Python 3.10-3.13 and
  Django 4.2-5.2.

[Unreleased]: https://github.com/mahmoudgshaker/drf-file-pipeline/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/mahmoudgshaker/drf-file-pipeline/releases/tag/v1.0.0
