# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-07-24

### Added

- Initial release.
- Token bucket, sliding window, and fixed window rate-limiting algorithms,
  implemented as atomic Redis Lua scripts (Redis Cluster compatible).
- `rate_limit()` factory producing DRF `BaseThrottle` subclasses for use
  in `throttle_classes`.
- `@ratelimit()` decorator for function-based views.
- Weighted request costs, plan-tier resolution, and composable key
  functions (IP, user, API key, tenant, endpoint).
- `RateLimit-Limit` / `RateLimit-Remaining` / `RateLimit-Reset` response
  headers, and `Retry-After` via DRF's `Throttled` exception.
- Full test suite across Python 3.10-3.13 and Django 4.2-5.2, including
  genuine multi-threaded concurrency tests.

[Unreleased]: https://github.com/mahmoudgshaker/drf-ratelimit-plus/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/mahmoudgshaker/drf-ratelimit-plus/releases/tag/v1.0.0
