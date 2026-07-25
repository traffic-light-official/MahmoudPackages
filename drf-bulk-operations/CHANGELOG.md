# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-07-25

### Added

- Initial release.
- `BulkCreateModelMixin`/`BulkUpdateModelMixin`/
  `BulkPartialUpdateModelMixin`/`BulkDestroyModelMixin`: `bulk_create`/
  `bulk_update`/`bulk_partial_update`/`bulk_destroy` actions accepting a
  JSON list body.
- `BulkModelViewSet`: all four mixins combined with
  `rest_framework.viewsets.ModelViewSet`.
- `ATOMIC` setting (default `True`): validate every item before any
  database write, aborting the whole batch with per-item errors if any
  item is invalid; set to `False` for independent per-item processing
  with a `207 Multi-Status` partial-success report.
- `MAX_BATCH_SIZE` setting to cap items per request.
- Per-object permission checks on update/destroy, matching DRF's own
  single-object mixins.
- Full test suite across Python 3.10-3.13 and Django 4.2-5.2.

[Unreleased]: https://github.com/MahmoudGShake/MahmoudPackages/compare/drf-bulk-operations-v1.0.0...HEAD
[1.0.0]: https://github.com/MahmoudGShake/MahmoudPackages/releases/tag/drf-bulk-operations-v1.0.0
