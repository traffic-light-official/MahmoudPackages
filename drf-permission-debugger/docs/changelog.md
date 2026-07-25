# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-07-25

### Added

- Initial release.
- `PermissionDebugMixin`: records a full trace of every configured
  permission class's outcome (granted/denied, message, code,
  request-level vs. object-level) for each request, with zero change to
  DRF's own authorization behavior.
- `PERMISSION_DEBUGGER` setting (`ENABLED`, `RESTRICT_TO_STAFF`,
  `HEADER_NAME`, `INCLUDE_IN_RESPONSE_BODY`) - opt-in and
  staff-restricted by default.
- `describe_permissions()`/`describe_view()`: static introspection of a
  view's permission/authentication/throttle stack with no live request.
- `show_view_permissions` management command.
- Full test suite across Python 3.10-3.13 and Django 4.2-5.2.

[Unreleased]: https://github.com/MahmoudGShake/MahmoudPackages/compare/drf-permission-debugger-v1.0.0...HEAD
[1.0.0]: https://github.com/MahmoudGShake/MahmoudPackages/releases/tag/drf-permission-debugger-v1.0.0
