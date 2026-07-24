# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-07-25

### Added

- Initial release.
- `problem_details_exception_handler`, a drop-in DRF `EXCEPTION_HANDLER`
  producing [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html) Problem
  Details responses, preserving DRF's own `WWW-Authenticate` / `Retry-After`
  header behavior and atomic-request rollback semantics.
- `CorrelationIdMiddleware` for correlation ID, request ID, and W3C
  `traceparent` trace ID propagation.
- Nested serializer validation error normalization
  (`normalize_validation_error`) into JSON-Pointer-style `errors` arrays.
- `ProblemRegistry` / `register` / `register_builder` for custom exception
  mapping, pre-populated with every built-in DRF exception and Django's
  `Http404` / `PermissionDenied`.
- `ProblemAPIException`, `ConflictError` (409), and
  `UnprocessableEntityError` (422) for application code to raise directly.
- Error catalog generation (`build_catalog`, `render_markdown`,
  `render_json`) and the `generate_error_catalog` management command.
- Optional `drf-spectacular` OpenAPI integration
  (`problem_details_postprocessing_hook`) registering the `ProblemDetail`
  schema component and default error responses.
- Localization support (`translate`, `activate_for_request`) built on
  Django's standard `Accept-Language` negotiation.
- Optional `drf-standardized-errors`-compatible response shape via the
  `STANDARDIZED_ERRORS_COMPAT` setting, for projects migrating from that
  package.
- Full test suite across Python 3.10-3.13 and Django 4.2-5.2.

[Unreleased]: https://github.com/MahmoudGShake/MahmoudPackages/compare/drf-error-response-standardizer-v1.0.0...HEAD
[1.0.0]: https://github.com/MahmoudGShake/MahmoudPackages/releases/tag/drf-error-response-standardizer-v1.0.0
