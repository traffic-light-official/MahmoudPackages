# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-07-25

### Added

- Initial release.
- `ProfileSerializerMixin`: per-field timing and per-field database
  query counts for any DRF serializer, aggregated across every row in
  a list response, with zero change to the serialized output.
- `ProfileSerializerViewMixin`: attaches an `X-Serializer-Profile`
  response header summarizing the slowest fields - opt-in and
  staff-restricted by default.
- `SERIALIZER_PROFILER` setting (`ENABLED`, `RESTRICT_TO_STAFF`,
  `HEADER_NAME`, `LOG_SLOW_FIELDS`, `SLOW_FIELD_THRESHOLD_MS`).
- Passive slow-field logging, independent of the header feature - safe
  for ongoing production monitoring.
- Full test suite across Python 3.10-3.13 and Django 4.2-5.2.

[Unreleased]: https://github.com/MahmoudGShake/MahmoudPackages/compare/drf-serializer-performance-profiler-v1.0.0...HEAD
[1.0.0]: https://github.com/MahmoudGShake/MahmoudPackages/releases/tag/drf-serializer-performance-profiler-v1.0.0
