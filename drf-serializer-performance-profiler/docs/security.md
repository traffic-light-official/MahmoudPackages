# Security

## The header reveals internal field names and their relative cost - treat it accordingly

`X-Serializer-Profile` exposes every serializer field's name and
timing/query count - useful for debugging, but also a hint about your
internal data model and implementation (which fields are computed,
which are expensive) that shouldn't reach an untrusted or ordinary
(non-staff) user. `ENABLED` defaults to `False` and `RESTRICT_TO_STAFF`
defaults to `True` specifically so that installing this package can
never, by itself, leak anything to a real user - both have to be
deliberately changed for that to become possible.

## `RESTRICT_TO_STAFF: False` should be rare and deliberate

Appropriate for a local development environment or an internal staging
environment with no real user data; inappropriate for anything
internet-facing with real accounts. If you need broader visibility in
a real environment, prefer a custom `finalize_response` override
checking a narrower condition instead of disabling the built-in
restriction wholesale - the same pattern documented for
`drf-permission-debugger`'s equivalent setting.

## `LOG_SLOW_FIELDS` never exposes anything over HTTP

This is the intentionally "always safe" mechanism: it only writes to
your application's own logs (`logger name
"drf_serializer_performance_profiler"`), never to a response. Field
names and timing data reach only whatever logging infrastructure you
already control - there's no `RESTRICT_TO_STAFF`-equivalent gate on it,
because there's no client-facing exposure to gate.

## Query counting doesn't reveal query *content*

`measure()` only counts how many `execute()` calls happen during a
field's rendering - it never captures the SQL text, bind parameters, or
results. A field's query *count* being visible in the header is not
equivalent to exposing what that query actually selects or contains.

## Timing data could theoretically enable a timing side-channel in a narrow case

If a field's timing depends on secret data in a way that's
distinguishable (e.g. a field that does more work only for certain
values), exposing precise per-field timing to a user who can trigger
requests could theoretically leak information about that data - this
is a general property of exposing any fine-grained timing information,
not specific to this package, and is exactly why the header is
staff-restricted by default rather than available to arbitrary
authenticated users.

## Dependency posture

This package's only runtime dependencies are Django and Django REST
Framework themselves - no third-party parsing or networking library.
Both are pinned to minimum versions in `pyproject.toml` and kept
current via Dependabot (see [Contributing](contributing.md)).

## Reporting a vulnerability

See [`SECURITY.md`](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-serializer-performance-profiler/SECURITY.md)
for the disclosure process. Do not open a public issue for a suspected
vulnerability.
