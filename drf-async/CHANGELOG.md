# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-07-25

### Added

- Initial release.
- `AsyncAPIView`: an async-native `dispatch()`, correctly bridging
  authentication, permission checks, and throttle checks (which may
  touch the database) through a thread via `sync_to_async`.
- `AsyncGenericAPIView` and 9 concrete generic views
  (`AsyncListAPIView`, `AsyncCreateAPIView`, etc.), mirroring
  `rest_framework.generics` one-to-one.
- `AsyncListModelMixin`/`AsyncCreateModelMixin`/`AsyncRetrieveModelMixin`/
  `AsyncUpdateModelMixin`/`AsyncDestroyModelMixin`, `AsyncGenericViewSet`,
  `AsyncReadOnlyModelViewSet`, `AsyncModelViewSet` - action methods
  named identically to DRF's sync mixins, so `DefaultRouter`/
  `SimpleRouter` route to them with no special handling.
- `BaseAsyncPermission`: write permission checks as native coroutines;
  existing sync `BasePermission` subclasses keep working unchanged.
- `BaseAsyncThrottle`/`AsyncSimpleRateThrottle`/`AsyncAnonRateThrottle`/
  `AsyncUserRateThrottle`: a genuinely async-native throttle
  implementation using Django's async cache API (`cache.aget`/`aset`).
- Full test suite across Python 3.10-3.13 and Django 4.2-5.2.

[Unreleased]: https://github.com/MahmoudGShake/MahmoudPackages/compare/drf-async-v1.0.0...HEAD
[1.0.0]: https://github.com/MahmoudGShake/MahmoudPackages/releases/tag/drf-async-v1.0.0
