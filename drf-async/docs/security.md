# Security

## Permission and authentication semantics are unchanged

`AsyncAPIView.acheck_permissions()`/`acheck_object_permissions()` call
exactly the same permission classes (sync or async) your project
already configures, in the same order, with the same
deny-if-any-check-fails semantics as `APIView.check_permissions()`.
This package changes *how* a check is executed (awaited directly vs.
bridged through a thread), never *what* it decides - converting a view
to `AsyncAPIView` does not, by itself, change who is authorized to
access it.

## `authentication_classes = []` changes which message a client sees, not who is authorized

DRF's `permission_denied()` raises `NotAuthenticated` (not your
denying permission's own `message`) whenever at least one authenticator
is configured but none of them successfully authenticated the request -
regardless of which permission actually rejected it. Setting
`authentication_classes = []` on a view only changes *which error
message and status nuance* a client sees for an unauthenticated
request; it does not weaken any permission check, and does not let an
unauthenticated request past a permission that denies it. See
[Troubleshooting](troubleshooting.md#my-permissions-message-is-being-replaced-with-a-generic-one).

## Bridging never widens what a sync permission/throttle can see or do

`call_maybe_async()` calls a sync permission/throttle's method with the
exact same `request`/`view`/`obj` arguments a synchronous `APIView`
would pass - `sync_to_async` only moves execution to a different
thread within the same request, it does not change scope, add
capabilities, or expose any additional state to the bridged callable.

## Throttle cache keys are as trustworthy as whatever built them

`AsyncSimpleRateThrottle.get_cache_key()` is your own code, exactly as
it is for DRF's own `SimpleRateThrottle` - if you build a cache key
from an unauthenticated, client-controlled header (as the example in
[Quick Start](quickstart.md#writing-an-async-native-throttle) does with
`X-Client-Id` for demonstration purposes only), a malicious client can
trivially defeat the rate limit by varying that header per request.
Key throttles that need to survive an adversarial client by
authenticated user ID or by `get_ident(request)` (client IP), not by a
client-supplied header, the same guidance that applies to DRF's own
`UserRateThrottle`/`AnonRateThrottle`.

## No user input reaches a file path, subprocess call, or dynamic code execution

Every value this package's code touches (headers, request bodies,
lookup kwargs) is only ever compared against known values, used as a
cache key, or handed to Django's ORM as parameterized query arguments -
never interpolated into a file path, shell command, or `eval`/`exec`.

## Dependency posture

This package's only runtime dependency beyond Django and Django REST
Framework themselves is `asgiref` (already a transitive dependency of
Django itself) - no additional third-party parsing or networking
library. All three are pinned to minimum versions in `pyproject.toml`
and kept current via Dependabot (see [Contributing](contributing.md)).

## Reporting a vulnerability

See [`SECURITY.md`](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-async/SECURITY.md)
for the disclosure process. Do not open a public issue for a suspected
vulnerability.
