# Deployment

## Checklist

- [ ] `drf_api_versioning` in `INSTALLED_APPS`.
- [ ] `DeprecationHeaderMixin` is only used on views whose
      `versioning_class` is one of *this package's* registry-aware
      schemes, not a plain DRF built-in one - `request.version` from an
      unvalidated scheme can be any string, and
      `registry.get_version_info()` raises `KeyError` (an unhandled
      500) for a name outside the registry, rather than the clean 404 a
      registry-aware scheme would already have produced before
      `finalize_response` is ever reached - see
      [Troubleshooting](troubleshooting.md).
- [ ] `ALLOW_SUNSET` is `False` (the default) in production, or its
      `True` override is a tracked, temporary state - see
      [Security](security.md#allow_sunset-true-is-a-deliberate-visible-override-keep-it-that-way).
- [ ] `list_api_versions` output is reviewed before every release that
      changes `API_VERSIONING` - a copy-paste date typo is otherwise
      only caught by a client complaint.
- [ ] If tracking usage via `deprecated_version_used`, the receiver is
      connected in `AppConfig.ready()`, not at module import time (the
      standard Django signal-wiring convention - see
      [Common Patterns](common-patterns.md#recording-per-client-deprecated-version-usage)).

## No database migrations, no persisted state

This package defines no models - there is nothing to migrate, and no
state persists between requests or between processes.

## Multi-region / multi-process deployments

`VersionInfo.is_deprecated()`/`is_sunset()` compare against Django's own
`timezone.now().date()`, which is consistent across processes as long
as `TIME_ZONE` (and `USE_TZ`) are configured identically across your
deployment - not the server's local system clock, which can differ
between hosts in different regions (see [Architecture](architecture.md)).

## Coordinating a version's actual removal

Declaring `sunset` and enforcing it (`ALLOW_SUNSET = False`) stops
requests from being *served*, but does not remove the version's own
routes/views/serializers from your codebase - plan a separate follow-up
release to actually delete the dead code once you've confirmed (via the
`deprecated_version_used` signal or access logs) that no client is
still trying to reach it.

## Rolling back a version's deprecation

Removing (or moving forward) a `deprecated`/`sunset` date takes effect
on the next process restart that picks up the new settings value - or
immediately, if using `@override_settings` in a running process is not
your deployment model (which it normally isn't; this applies to normal
settings-file changes plus a redeploy, same as any other Django
setting).
