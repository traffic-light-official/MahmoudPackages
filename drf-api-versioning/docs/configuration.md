# Configuration

All configuration lives under a single Django setting, `API_VERSIONING`
- see [Settings](settings.md) for the complete reference.

## The registry is the single source of truth

Once `API_VERSIONING["VERSIONS"]` is declared, every registry-aware
versioning class computes `allowed_versions`/`default_version` from it
directly - DRF's own global `ALLOWED_VERSIONS`/`DEFAULT_VERSION`
settings (`REST_FRAMEWORK = {...}`) are not consulted at all by this
package's classes. If you switch an existing view from a DRF built-in
scheme to this package's equivalent, remove any per-view
`allowed_versions = [...]` override too - it would otherwise silently
have no effect (the registry-aware property always wins).

## Choosing dates

`deprecated`/`sunset` are plain `datetime.date` (or `datetime.datetime`,
normalized to a date) objects, compared against
`django.utils.timezone.now().date()` - Django's own current date,
respecting `USE_TZ`/`TIME_ZONE`, not the server process's raw system
clock. A version becomes deprecated/sunset at midnight on the
configured date, in Django's configured timezone.

## Choosing `ALLOW_SUNSET`

Leave `ALLOW_SUNSET = False` (the default) in essentially every case -
a version past its sunset date should actually stop working, or the
sunset date was meaningless. The one legitimate use for `True` is a
staged rollout: deploy the sunset date first (so `list_api_versions`
and monitoring reflect it, and `Sunset` headers start appearing) with
enforcement still off, confirm no unexpected traffic remains, then flip
to `False` to actually enforce it - see
[Common Patterns](common-patterns.md#staging-a-sunset-date-before-enforcing-it).

## Customizing header names

`DEPRECATION_HEADER`/`SUNSET_HEADER`/`LINK_HEADER` default to the
standard names (`Deprecation`, `Sunset`, `Link`) - only override these
if an existing client integration already expects different header
names; there is no standards-based reason to rename them otherwise.
