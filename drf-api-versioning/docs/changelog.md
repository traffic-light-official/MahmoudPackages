# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-07-25

### Added

- Initial release.
- A version registry (`API_VERSIONING` setting) declaring every
  supported version's deprecation/sunset dates and migration link.
- Registry-aware versioning schemes (`URLPathVersioning`,
  `NamespaceVersioning`, `AcceptHeaderVersioning`,
  `QueryParameterVersioning`, `HostNameVersioning`) - drop-in
  replacements for DRF's own, validated against the registry.
- `UnknownAPIVersionError` and `APIVersionSunsetError` (410), raised
  automatically for unregistered or sunset versions, preserving each
  wrapped scheme's own native status code for unknown versions.
- `DeprecationHeaderMixin`: automatic `Deprecation`/`Sunset`/`Link`
  response headers (RFC 8594-style) for deprecated/sunset versions.
- `deprecated_version_used` signal for custom usage analytics.
- The `list_api_versions` management command.
- Full test suite across Python 3.10-3.13 and Django 4.2-5.2.

[Unreleased]: https://github.com/MahmoudGShake/MahmoudPackages/compare/drf-api-versioning-v1.0.0...HEAD
[1.0.0]: https://github.com/MahmoudGShake/MahmoudPackages/releases/tag/drf-api-versioning-v1.0.0
