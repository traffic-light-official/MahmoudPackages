# Performance

## Access token verification is stateless

`JWTAuthentication.authenticate()` verifies a JWT's signature and expiry
in-process - no database query, no cache lookup - by default. This is
the primary performance benefit of using JWTs at all: authenticating a
request costs a signature check (fast, symmetric HMAC by default), not a
network round trip. Enabling `CHECK_DEVICE_REVOCATION_ON_AUTH` adds
exactly one indexed query (`Device.objects.filter(pk=..., revoked_at__isnull=True).exists()`)
per authenticated request - only enable it if immediate revocation is a
hard requirement.

## Login cost

A `POST /auth/login/` call performs, at most:

- One `authenticate()` call (Django's own password hasher - deliberately
  slow, by design, to resist brute forcing; this dominates login latency
  regardless of this package).
- One MFA check (`TOTPDevice` lookup + local HMAC computation - negligible).
- One `Device` insert, one `RefreshToken` insert.
- One `LoginHistory` insert (skip via `LOGIN_HISTORY_ENABLED = False` if
  you don't need it, though the write is a single indexed insert either
  way).

## Refresh cost

`rotate_refresh_token()` performs one `SELECT ... FOR` via
`select_related("device")` (a single query, joined), up to one `UPDATE`
(the old token), one `INSERT` (the new token), and one `UPDATE` (the
device's `last_used_at`) - four queries total on the common path, none
of them table scans (`jti` is the primary key; `Device` lookups are by
primary key via the join).

## Reuse detection adds no extra cost on the happy path

The "is this token still active" check is the same `SELECT` already
needed to look up the token by `jti` - reuse detection is a branch on
data already fetched, not an additional query.

## Indexes

`Device` is indexed on `(user, revoked_at)` (the shape
`revoke_all_devices` and `DeviceViewSet.get_queryset` use).
`RefreshToken` is indexed on `(device, revoked_at)`. `LoginHistory` is
indexed on `(user, created_at)`.

## Token size

Access and refresh tokens carry a handful of short claims (`user_id`,
`token_type`, `device_id`, `jti`, `iat`/`exp`) - a few hundred bytes
signed with HS256, small enough to be a negligible addition to request
header size even on mobile networks. Avoid adding large custom claims;
put anything beyond a small identifier in a database row the token
merely points to (as `Device`/`RefreshToken` already do).
