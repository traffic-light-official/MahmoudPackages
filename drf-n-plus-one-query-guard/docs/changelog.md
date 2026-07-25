# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-07-25

### Added

- Initial release.
- `QueryTracker`: captures every SQL query executed within a scope via
  Django's public `connection.execute_wrapper()` hook, across every
  configured database alias.
- Fingerprint-based repeated-query detection (not just a total query
  count) - a query fingerprint repeating at least `THRESHOLD` times is
  reported as a suspected N+1, with the originating application call
  site.
- `assert_no_n_plus_one()`: a test-time context manager, independent of
  any Django setting.
- `NPlusOneGuardMiddleware`: guards every request, with a
  `warn`/`raise`/`report` mode and an opt-in `DEBUG`-only response
  header.
- `guard_view()`: a per-view/per-action decorator.
- Full test suite across Python 3.10-3.13 and Django 4.2-5.2.

[Unreleased]: https://github.com/MahmoudGShake/MahmoudPackages/compare/drf-n-plus-one-query-guard-v1.0.0...HEAD
[1.0.0]: https://github.com/MahmoudGShake/MahmoudPackages/releases/tag/drf-n-plus-one-query-guard-v1.0.0
