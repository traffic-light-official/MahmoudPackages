# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-07-24

### Added

- Initial release.
- `TenantScopedModel` — abstract base with automatic tenant scoping and
  save-time enforcement (auto-assign on create, reject cross-tenant
  saves).
- `TenantManager` / `TenantQuerySet` — every query automatically
  filtered to the current tenant, with an explicit `unscoped()` escape
  hatch.
- `TenantMiddleware` — resolves the current tenant per request via a
  configurable resolver (header, subdomain, or user attribute) and
  binds it to an async-safe `contextvars`-based context.
- `TenantScopedSerializerMixin` / `TenantScopedModelSerializer` —
  auto-assigns the tenant on create and rejects cross-tenant relations.
- `IsTenantMember` — DRF permission for object-level tenant enforcement.
- `TenantAdminMixin` — scopes the Django admin to the current tenant
  (superusers see every tenant).
- `drf_multitenant.cache` — per-tenant cache key namespacing on top of
  Django's own cache framework.
- `drf_multitenant.testing` — `as_tenant()`, `as_no_tenant()`, and
  `assert_no_cross_tenant_leak()` test helpers.
- Full test suite across Python 3.10-3.13 and Django 4.2-5.2.

[Unreleased]: https://github.com/mahmoudgshaker/drf-multitenant/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/mahmoudgshaker/drf-multitenant/releases/tag/v1.0.0
