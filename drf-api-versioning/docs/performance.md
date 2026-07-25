# Performance

## No database, no cache, no I/O

`registry.get_version_info()` reads directly from the already-cached,
in-memory `API_VERSIONING` setting (`settings._ApiVersioningSettings`'s
`cached_property`, invalidated only on `setting_changed`) - there is no
database query, cache backend call, or file I/O anywhere in this
package's request-handling path. Resolving and validating a version
costs a handful of dict lookups and date comparisons.

## `allowed_versions`/`default_version` as properties add no measurable overhead

Since versioning scheme instances are already constructed fresh
per-request by DRF itself (`self.versioning_class()`), computing these
as properties instead of plain attributes changes nothing about
allocation cost - it's a property lookup returning an already-materialized
tuple/string, not a fresh computation each time (the settings object's
own `cached_property` already did the real work once).

## The signal only fires for deprecated versions, never for every request

`deprecated_version_used.send(...)` is only called inside the
`info.is_deprecated()` branch - a request to a fully-supported version
never touches Django's signal dispatch machinery at all. If you have
zero receivers connected, `Signal.send()` itself is cheap (iterates an
empty receiver list), but this package doesn't even pay that cost for
the common case of a non-deprecated version.

## Header injection only runs `finalize_response`'s own extra branch, no template rendering

`DeprecationHeaderMixin.finalize_response` calls `super()` first (so
whatever the view already does is unaffected), then does at most three
dict-like `response[...] = ...` assignments and one
`format_datetime()` call per header - no template engine, no
serialization step, negligible compared to the cost of serializing the
actual response body.

## Recommended: don't recompute `get_version_info` when you already have it

If you need a version's metadata in multiple places within one request
(e.g. both a custom header and application logic), call
`registry.get_version_info(request.version)` once and reuse the result,
rather than calling it repeatedly - each call re-reads the (already
cached) settings dict and re-normalizes dates, which is cheap but
unnecessary to repeat.
