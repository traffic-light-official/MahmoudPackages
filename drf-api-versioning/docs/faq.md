# FAQ

## Why doesn't this package ship a usage-tracking model?

"Usage" means different things to different projects - per-request,
per-authenticated-user, per-API-key, aggregated hourly vs. daily, kept
for 30 days vs. a year. Bundling a model would mean either a narrow,
opinionated schema most projects would need to work around, or a
maintenance burden supporting a config surface trying to cover every
variant. `deprecated_version_used` gives you the exact moment and
context (request, version, metadata) to record however your project
already does analytics - see
[Common Patterns](common-patterns.md#recording-per-client-deprecated-version-usage).

## Does this replace DRF's own versioning settings (`DEFAULT_VERSION`, `ALLOWED_VERSIONS`)?

For any view using one of this package's versioning classes, yes -
`allowed_versions`/`default_version` are computed from the
`API_VERSIONING` registry, and DRF's own `REST_FRAMEWORK` settings for
these are not consulted by those classes at all (they remain in effect
for any *other* view still using DRF's plain built-in classes). See
[Configuration](configuration.md#the-registry-is-the-single-source-of-truth).

## Can I use a version name that isn't `"v1"`/`"v2"`-shaped?

Yes - any non-empty string works as a version name (`"2026-01"`,
`"beta"`, `"stable"`) since the registry never assumes a particular
naming convention. Whatever scheme you use to resolve the version from
a request (URL segment, header parameter, etc.) is responsible for
producing a string that matches a registered name.

## What happens if I remove a version from `VERSIONS` while it's still receiving traffic?

Every request resolving to that version now fails
`is_allowed_version()` in the wrapped DRF scheme (since
`allowed_versions` no longer includes it), converted to
`UnknownAPIVersionError` (404, or 406 for `AcceptHeaderVersioning`) -
the same as any other never-registered version. There is no grace
period for "recently removed" - use `sunset` (with `ALLOW_SUNSET`
staged as described in [Common Patterns](common-patterns.md#staging-a-sunset-date-before-enforcing-it))
instead of deleting the entry outright if you need a transition window.

## Does `DeprecationHeaderMixin` work with `ViewSet`/`GenericAPIView`/plain `APIView`?

Yes - `finalize_response` is defined on `APIView` itself and inherited
by every DRF view base class, so the mixin works identically regardless
of which one you use.

## Can I use more than one versioning scheme in the same project?

Yes - different views can use different registry-aware classes freely
(e.g. `URLPathVersioning` for most endpoints, `AcceptHeaderVersioning`
for one legacy integration) - they all read the same shared registry,
so a version's deprecation/sunset status is consistent regardless of
which scheme resolved it.

## Why is `AcceptHeaderVersioning`'s unknown-version error a 406 while the others are 404?

By design - see
[Architecture](architecture.md#the-unknown-version-status-code-matches-the-wrapped-schemes-own-convention).

## Does this package support semantic versioning (`1.2.3`) instead of `v1`/`v2`?

The registry itself is agnostic to the naming scheme (see above), but
none of the five versioning schemes parse a version string beyond exact
string matching against `allowed_versions` - there is no
"1.x is compatible with 1.y" range logic. If you need that, resolve to
a coarser version identifier (e.g. major version only) before it
reaches this package's schemes.
