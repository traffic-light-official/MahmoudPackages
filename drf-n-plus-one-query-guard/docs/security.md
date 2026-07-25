# Security

## Never enable `MODE = "raise"` for the middleware in production

`NPlusOneGuardMiddleware` with `MODE = "raise"` turns a suspected N+1 -
a performance issue, not a correctness one - into an unhandled exception
propagating out of every affected request, typically a 500 response for
real users. This is exactly the intended behavior for
development/CI/staging (fail loudly and immediately, before the code
ships), but is a self-inflicted availability risk in production: a
change elsewhere in the codebase, or organic data growth crossing
`THRESHOLD` for the first time, could turn a previously-fine endpoint
into a hard failure for every user hitting it, with no code change of
its own. Use `"warn"` or `"report"` in production - both only ever
observe, never fail the request.

## The `DEBUG`-only response header is a deliberate, hard gate

`NPlusOneGuardMiddleware` only ever adds its `RESPONSE_HEADER`
(`X-N-Plus-One-Warnings` by default) when `settings.DEBUG` is `True` -
checked directly against `django.conf.settings.DEBUG`, not against
`MODE` or any other configurable value. This is intentional and
non-configurable: the header's content includes normalized SQL text and
table names, which is internal implementation detail that should never
be exposed to a production client regardless of how `N_PLUS_ONE_GUARD`
is configured. If you need this information in production, log it
server-side via `MODE = "warn"` instead of trying to make the header
available there.

## Call-site information never includes query parameter *values*

`QueryEvent.sql` (and therefore `Violation.sample_sql`, and any
message/log line derived from it) is the query's parameterized SQL
text - placeholders, not the literal values that were bound to them
(see [Architecture](architecture.md#why-no-literal-stripping-is-needed)).
A violation message can never leak a specific user's ID, email, or any
other parameter value that happened to trigger the detected pattern,
even in `"warn"` mode's log output.

## No network access, no subprocess, no external service

This package reads Django's own query execution stream via a public,
in-process hook and writes to the standard `logging` module or raises a
plain Python exception - there is no outbound network call, no
subprocess invocation, and no third-party service integration anywhere
in its execution path.

## Dependency posture

This package's only runtime dependencies are Django and Django REST
Framework themselves - no third-party parsing or instrumentation
library. Both are pinned to minimum versions in `pyproject.toml` and
kept current via Dependabot (see [Contributing](contributing.md)).

## Reporting a vulnerability

See [`SECURITY.md`](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-n-plus-one-query-guard/SECURITY.md)
for the disclosure process. Do not open a public issue for a suspected
vulnerability.
