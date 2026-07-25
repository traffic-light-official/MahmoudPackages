# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-07-25

### Added

- Initial release.
- `diff_schemas()`: structural OpenAPI diff engine covering paths,
  operations, parameters, request bodies, and response schemas,
  including nested object/array fields with `$ref` resolution.
- An explicit, documented breaking vs. non-breaking classification for
  every detected change kind.
- Four renderers: Markdown, self-contained HTML, Slack Block Kit (with
  an optional webhook-posting helper), and GitHub Release notes.
- `git_utils.load_schema_at_ref()`: read a schema as committed at a Git
  tag/branch/commit via `git show`, no checkout required.
- The `drf-changelog-generator` console script CLI, with
  `--fail-on-breaking` for CI gating.
- A ready-to-use composite GitHub Action (`action.yml`).
- The optional `generate_changelog` Django management command, diffing
  the current `drf-spectacular` schema against a previous Git ref.
- Full test suite across Python 3.10-3.13 and Django 4.2-5.2.

[Unreleased]: https://github.com/MahmoudGShake/MahmoudPackages/compare/drf-changelog-generator-v1.0.0...HEAD
[1.0.0]: https://github.com/MahmoudGShake/MahmoudPackages/releases/tag/drf-changelog-generator-v1.0.0
