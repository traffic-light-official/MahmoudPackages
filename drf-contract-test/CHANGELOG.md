# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-07-24

### Added

- Initial release.
- `compare_schemas()` — directionally-correct breaking-change detection
  between two OpenAPI schema snapshots (request-side widening is safe,
  narrowing is breaking; response-side is the reverse).
- `generate_contract_cases()` / `validate_response_against_schema()` —
  generating and validating contract tests from an OpenAPI schema.
- `check_version_bump()` — enforcing an API version bump alongside
  breaking changes.
- `drf-contract-test` CLI with `snapshot`, `compare`, and `check`
  subcommands.
- Pytest plugin (`drf_contract_test.pytest_plugin`) with fixtures and an
  assertion helper.
- JSON and HTML report renderers.
- Full test suite across Python 3.10-3.13 and Django 4.2-5.2.

[Unreleased]: https://github.com/mahmoudgshaker/drf-contract-test/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/mahmoudgshaker/drf-contract-test/releases/tag/v1.0.0
