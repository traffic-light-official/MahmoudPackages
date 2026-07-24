# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-07-24

### Added

- Initial release.
- `IdempotencyMiddleware` for project-wide idempotency handling.
- `@idempotent` decorator for per-view opt-in.
- Pluggable backend interface (`BaseBackend`) with `RedisBackend` and
  `DatabaseBackend` implementations.
- Request fingerprinting to detect and reject idempotency-key reuse with
  a different request body.
- Atomic lock acquisition preventing concurrent duplicate execution.
- TTL-based expiry (native in Redis; `cleanup_expired_idempotency_keys`
  management command for the database backend).
- `get_idempotency_status` for status tracking.
- Full test suite across Python 3.10-3.13 and Django 4.2-5.2.

[Unreleased]: https://github.com/mahmoudgshaker/drf-idempotency/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/mahmoudgshaker/drf-idempotency/releases/tag/v1.0.0
