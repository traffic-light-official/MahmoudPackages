# Security

## This is a debugging tool that reveals internal security logic - treat it accordingly

The whole point of `PermissionDebugMixin` is to expose *why* a
permission decision was made - which is exactly the kind of
information that should never reach an untrusted, unauthenticated, or
ordinary (non-staff) user. `ENABLED` defaults to `False` and
`RESTRICT_TO_STAFF` defaults to `True` specifically so that installing
this package can never, by itself, leak anything to a real user - both
have to be deliberately changed for that to become possible.

## `RESTRICT_TO_STAFF: False` should be rare and deliberate

Setting `RESTRICT_TO_STAFF` to `False` exposes the trace header (and
body, if also configured) to **every** requester, including anonymous
ones - this is appropriate for a local development environment or an
internal staging environment with no real user data, and inappropriate
for anything internet-facing with real accounts. If you need broader
visibility than "staff only" in a real environment, prefer a custom
`finalize_response` override checking a narrower condition (a specific
permission group, an internal IP allowlist, a feature flag) instead of
disabling the built-in restriction wholesale - see
[Advanced Usage](advanced-usage.md#restricting-the-trace-to-a-specific-subset-of-staff).

## The trace reveals your permission class names, not their internal logic

`X-Permission-Trace: IsAuthenticated=granted, HasActiveSubscription=denied`
tells a staff user which named permission classes exist and their
outcome - it does not reveal `HasActiveSubscription`'s actual
implementation (what it checks internally, what data it queries). If
your permission class names themselves are sensitive (unlikely, but
possible in a design where the mere existence of a check is
confidential), avoid enabling this package for that specific viewset,
or write a custom trace-formatting override that redacts class names
you don't want surfaced.

## `message`/`code` are only ever the permission class's own, already-public attributes

`PermissionCheckResult.message`/`.code` come directly from the
permission instance's `.message`/`.code` attributes - the exact same
values DRF's own `permission_denied()` already puts in a `403`
response's `detail` field for the denying permission (just made
visible for *every* checked permission, not only the one that actually
denied). Nothing is captured here that a plain, undecorated view
wouldn't already expose for the specific denying class.

## Never disable `RESTRICT_TO_STAFF` to work around an authentication problem

If you're tempted to set `RESTRICT_TO_STAFF: False` because tracing
"isn't showing up" for a user you expected to see it, that's very
likely the setting working as intended (see
[Troubleshooting](troubleshooting.md)) - fix the actual condition (log
in as staff, or use the response-body option locally) rather than
weakening the default for every user in that environment.

## Dependency posture

This package's only runtime dependencies are Django and Django REST
Framework themselves - no third-party parsing or networking library.
Both are pinned to minimum versions in `pyproject.toml` and kept
current via Dependabot (see [Contributing](contributing.md)).

## Reporting a vulnerability

See [`SECURITY.md`](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-permission-debugger/SECURITY.md)
for the disclosure process. Do not open a public issue for a suspected
vulnerability.
