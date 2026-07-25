# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-07-25

### Added

- Initial release.
- Short-lived, stateless JWT access tokens and rotating refresh tokens
  delivered via httpOnly, Secure, SameSite cookies.
- Refresh token rotation with reuse detection: replaying an
  already-rotated refresh token revokes its entire token family.
- Double-submit-cookie CSRF protection for cookie-authenticated
  refresh/logout endpoints.
- `Device` and `LoginHistory` models: per-device session management,
  `logout` (current device), `logout-all` (every device), and device
  listing/revocation.
- "Remember me" long-lived refresh tokens.
- `MFAProvider` extension hook interface, with a built-in RFC 6238 TOTP
  implementation (`TOTPProvider`).
- `JWTAuthentication` DRF authentication class (Bearer access tokens).
- `LoginView`, `RefreshView`, `LogoutView`, `LogoutAllView`,
  `DeviceViewSet`, `LoginHistoryViewSet`, and a ready-to-`include()`
  `drf_jwt_auth_kit.urls`.
- Django admin registration for every model.
- Full test suite across Python 3.10-3.13 and Django 4.2-5.2.

[Unreleased]: https://github.com/MahmoudGShake/MahmoudPackages/compare/drf-jwt-auth-kit-v1.0.0...HEAD
[1.0.0]: https://github.com/MahmoudGShake/MahmoudPackages/releases/tag/drf-jwt-auth-kit-v1.0.0
