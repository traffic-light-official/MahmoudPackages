# Troubleshooting

## `POST /auth/refresh/` always returns 403

`validate_csrf()` runs before anything else in `RefreshView`/`LogoutView`.
Confirm you are:

1. Sending the `refresh_csrftoken` cookie's **current** value (it
   rotates on every successful login/refresh - a header captured earlier
   in a session will not match after a subsequent refresh).
2. Echoing it in the exact header named by the `CSRF_HEADER_NAME`
   setting (`X-Refresh-CSRFToken` by default).
3. Actually sending cookies at all - a cross-origin `fetch()` needs
   `credentials: "include"`, and `same-origin` (the default) only sends
   cookies for same-origin requests.

## `POST /auth/refresh/` returns 401 for a token that should still be valid

Check, in this order:

1. Has this exact refresh token already been used once? Rotation means
   each refresh token is single-use; a second use of the *same* token is
   reuse detection, not a bug - see
   [FAQ](faq.md#what-happens-if-a-refresh-token-is-used-twice).
2. Has the device been revoked (logout, logout-all, or a prior reuse
   detection event)? Check `Device.revoked_at`/`revoked_reason`.
3. Has `REFRESH_TOKEN_LIFETIME` actually elapsed? Check
   `RefreshToken.expires_at`.

## `JWTAuthentication` always returns 401 "Invalid access token"

Confirm the `Authorization` header is exactly `Bearer <token>` (the
scheme is case-sensitive and must match `AUTH_HEADER_PREFIX`, `"Bearer"`
by default) and that you are sending an **access** token, not a refresh
token - `LoginView`/`RefreshView` responses put the access token in the
JSON body (`access_token`), not in a cookie.

## Login always succeeds even though I enabled MFA

`is_required()` only returns `True` for a user with a **confirmed**
`TOTPDevice` row - starting enrollment (`POST /auth/mfa/totp/setup/`)
alone does not enable MFA; the user must also call `/confirm/` with a
valid code. Also confirm `MFA_PROVIDER` is actually set to
`"drf_jwt_auth_kit.mfa.TOTPProvider"` (the package default,
`NullMFAProvider`, never requires MFA).

## TOTP codes from the authenticator app are always rejected

1. Confirm the server and the device generating codes have
   reasonably synchronized clocks - TOTP is time-based; if the server's
   clock is off by more than `TOTP_VALID_WINDOW * 30` seconds, every code
   will be rejected.
2. Confirm you scanned/entered the `provisioning_uri`/`secret` returned
   by `/auth/mfa/totp/setup/` **exactly** - re-running setup generates a
   brand new secret, invalidating a previously scanned QR code.

## `ImproperlyConfigured: The 'JWT_AUTH_KIT' Django setting must be a dict`

`JWT_AUTH_KIT` must be a `dict`, even if empty: `JWT_AUTH_KIT = {}`.

## `ImproperlyConfigured: 'JWT_AUTH_KIT["REFRESH_COOKIE_SAMESITE"]' of "None" requires ... "REFRESH_COOKIE_SECURE" to be True`

Browsers reject a `SameSite=None` cookie that isn't also marked
`Secure`. Set `REFRESH_COOKIE_SECURE = True` (the default) if you need
`SameSite=None` for a cross-site SPA.

## Tests fail with `AppRegistryNotReady`

If you're extending this package and add a new top-level import to
`drf_jwt_auth_kit/__init__.py`, make sure it does not transitively
import `drf_jwt_auth_kit.models` (or `drf_jwt_auth_kit.mfa`, which
touches the `TOTPDevice` model) - see the note at the top of that
module. Django imports every app's `__init__.py` before any app's
models are ready.

## Login history fills up with entries I don't want

Set `LOGIN_HISTORY_ENABLED = False` to stop recording entirely, or
periodically prune old rows yourself (this package does not provide a
built-in retention/cleanup command for `LoginHistory`, unlike
`cleanup_expired_tokens` for `RefreshToken`, since retention policy for
an audit trail is a project-specific compliance decision).
