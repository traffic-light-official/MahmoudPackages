# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-07-25

### Added

- Initial release.
- `scaffold()`: generate DRF `serializers.py`, `views.py`, and `urls.py`
  from an OpenAPI contract, with dependency-ordered serializer classes
  and `$ref`-aware nested field generation.
- Idempotent regeneration via marker-delimited generated regions
  (`drf_api_reverse.regions`) - hand-written code survives a re-run.
- `check_drift()`/`raise_if_drifted()`: detect when on-disk generated
  code no longer matches what the current contract would produce.
- The `drf-api-reverse` console script CLI (`scaffold`/`check`
  subcommands).
- The optional `scaffold_api` Django management command.
- Full test suite across Python 3.10-3.13 and Django 4.2-5.2.

[Unreleased]: https://github.com/MahmoudGShake/MahmoudPackages/compare/drf-api-reverse-v1.0.0...HEAD
[1.0.0]: https://github.com/MahmoudGShake/MahmoudPackages/releases/tag/drf-api-reverse-v1.0.0
