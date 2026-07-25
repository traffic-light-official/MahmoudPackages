# Troubleshooting

## `KeyError` raised from inside `DeprecationHeaderMixin.finalize_response`

This means `request.version` resolved to a string not present in
`API_VERSIONING["VERSIONS"]` - which should be impossible if the view's
`versioning_class` is one of this package's own registry-aware schemes
(they validate against the registry before `request.version` is ever
set), but happens readily if the view still uses a **plain DRF**
versioning class (`rest_framework.versioning.URLPathVersioning`, etc.)
alongside `DeprecationHeaderMixin` - that combination lets an
unvalidated version reach the mixin. Fix: use the matching class from
`drf_api_versioning.versioning` instead of DRF's own. See
[Deployment](deployment.md#checklist).

## `ImproperlyConfigured: 'API_VERSIONING["VERSIONS"]' must declare at least one version`

`VERSIONS` is empty (or `API_VERSIONING` itself is unset) - unlike most
settings in this workspace's packages, there is no usable "zero
versions declared" default; declare at least one.

## `ImproperlyConfigured: 'API_VERSIONING["DEFAULT_VERSION"]' (...) must be a key in ...`

`DEFAULT_VERSION` must exactly match one of `VERSIONS`'s keys, or be
`None` - a typo (`"V1"` vs `"v1"`) is the most common cause.

## `ImproperlyConfigured: ... "sunset" cannot be earlier than "deprecated"`

A version's `sunset` date is before its `deprecated` date - almost
always a copy-paste or typo error (check the exact dates in that
version's dict), since sunsetting a version implies it was already
deprecated no later than that point.

## A version I expected to be rejected (404/410) returns 200 instead

1. Confirm the view's `versioning_class` is actually one of
   `drf_api_versioning.versioning`'s classes, not DRF's own - only the
   registry-aware ones enforce anything.
2. For a 410 specifically, confirm `ALLOW_SUNSET` isn't `True` (checked
   at request time, not at settings-definition time) - see
   [Configuration](configuration.md#choosing-allow_sunset).
3. Confirm the version's `sunset` date has actually passed as of
   *today*, in Django's configured timezone, not the date you expect
   from a different timezone - see
   [Architecture](architecture.md#dates-are-compared-using-djangos-current-date-not-the-system-clocks).

## `NamespaceVersioning` always resolves to the default version, ignoring the URL's namespace

Confirm the URL is actually reached through a namespaced `include()` -
`resolver_match.namespace` is empty for any URL not registered inside
one, and `NamespaceVersioning.determine_version` returns
`default_version` directly (without validating it) whenever there's no
namespace at all - see
[Architecture](architecture.md#namespaceversioning-is-the-one-scheme-where-an-unresolved-version-can-reach-the-registry-as-none).

## `HostNameVersioning` always resolves to the default version

`HostNameVersioning.hostname_regex` requires a three-part hostname
(`subdomain.domain.tld`) - a bare `"testserver"` (Django's test client
default) or a two-part production domain never matches, and silently
falls back to `default_version`. Set `HTTP_HOST` explicitly in tests
(`api_client.get(path, HTTP_HOST="v1.example.com")`), and confirm the
hostname is in `ALLOWED_HOSTS`.

## `DisallowedHost` when testing `HostNameVersioning`

Add the test hostname (or a wildcard, in tests only) to `ALLOWED_HOSTS`
- Django rejects any `Host` header not in that list before this
package's code ever runs.

## The `Deprecation`/`Sunset` header value looks wrong (wrong day, wrong timezone)

Both are formatted as an HTTP-date at **midnight UTC** for the
configured date - `datetime.date(2026, 1, 1)` always becomes
`Thu, 01 Jan 2026 00:00:00 GMT`, regardless of `TIME_ZONE`. If you
expected a different time-of-day, that's expected: RFC 8594's `Sunset`
header (and this package's `Deprecation` header, formatted the same
way) is a date-granularity signal, not a precise timestamp.
