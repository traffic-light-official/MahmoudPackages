# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-07-24

### Added

- Initial release.
- `PartialFieldsSerializerMixin`, `PartialFieldsSerializer`, and
  `PartialFieldsModelSerializer` for sparse-fieldset serialization.
- `PartialResponseMixin` for automatic view/queryset wiring.
- Nested field selection, exclusion (`-field`), aliasing (`alias:field`),
  and wildcard (`*`) syntax in the `fields` query parameter.
- Automatic `select_related` / `prefetch_related` / `only()` query
  optimization based on the requested fields, including recursive
  optimization of nested `Prefetch` querysets.
- `requires_related` decorator for declaring optimizer hints on
  `SerializerMethodField` methods.
- Optional `drf-spectacular` integration (`PartialResponseAutoSchema`,
  `fields_query_parameter`).
- Full test suite across Python 3.10–3.13 and Django 4.2–5.2.

[Unreleased]: https://github.com/mahmoudgshaker/drf-partial-response-fields/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/mahmoudgshaker/drf-partial-response-fields/releases/tag/v1.0.0
