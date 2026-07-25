# Security

This page covers security considerations specific to
`drf-jwt-auth-kit`. For the general vulnerability reporting process, see
[SECURITY.md](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-jwt-auth-kit/SECURITY.md).

## Refresh tokens are httpOnly by design

The refresh cookie is always set with `HttpOnly` - JavaScript cannot
read it, even via a successful XSS injection. Do not build a "read the
refresh token in JS" workaround; if a client genuinely cannot use
cookies, use the header-based mobile pattern in
[Examples](examples.md#mobile-client-no-cookie-jar) instead, and treat
the raw refresh token with the same care as a password (secure storage,
never logged).

## CSRF protection is required and enabled by default

`RefreshView` and `LogoutView` validate a double-submit CSRF token on
every request (see [Architecture](architecture.md#csrf-is-double-submit-cookie-not-djangos-built-in-csrf-middleware)).
Do not disable this or bypass `validate_csrf()` if you build custom
cookie-authenticated endpoints on top of this package's cookies.

## Reuse detection and its blast radius

Detecting a replayed, already-rotated refresh token revokes the *entire*
device (every refresh token that device has, including ones that
haven't been used yet). This is intentional: a stolen token means the
whole session is compromised, not just the one token. Users are simply
prompted to log in again - the alternative (only revoking the specific
stolen token) risks leaving an attacker's freshly-rotated copy valid.

## Access token exposure window

Because access tokens are verified statelessly, a stolen access token
remains valid until it naturally expires, even after a `logout-all`.
`ACCESS_TOKEN_LIFETIME` (default 5 minutes) directly bounds this window
- do not raise it significantly without also enabling
`CHECK_DEVICE_REVOCATION_ON_AUTH` if your threat model requires faster
revocation.

## Password verification

`LoginView` uses Django's own `django.contrib.auth.authenticate()`,
which uses Django's configured password hashers (PBKDF2/Argon2/etc.) and
their built-in timing-attack resistance. This package does not
re-implement or bypass any part of Django's password verification.

## TOTP secrets

`TOTPDevice.secret` is stored as plaintext base32 in the database (this
is standard practice for TOTP - unlike a password, a TOTP secret must be
retrievable to compute the current valid code, so it cannot be hashed).
Protect it the same way you protect any other sensitive column: database
access controls, encryption at rest, and it is marked `readonly` in the
Django admin so it is never editable through that UI after creation.

## MFA codes are verified with tolerance, not exactly

`verify_totp_code()` checks a window of `TOTP_VALID_WINDOW` steps (30
seconds each) around the current time to tolerate clock drift between
server and authenticator app. Widening this window trades a small amount
of brute-force resistance for more clock-drift tolerance - the default
of 1 (90 total seconds of tolerance) is a reasonable balance; avoid
setting it much higher.

## Login history and IP addresses

`LoginHistory.ip_address` is derived from `X-Forwarded-For` (first
value) if present, else `REMOTE_ADDR`. If your deployment is not behind
a trusted reverse proxy that sets `X-Forwarded-For` correctly, a client
can spoof this header - only trust it if you control the network path
between your load balancer and the application server.

## Dependency security

- Run `pip audit` regularly against your dependency tree.
- Keep Django, Django REST Framework, and PyJWT up to date. PyJWT
  security advisories (algorithm confusion attacks, etc.) directly
  affect this package's token verification.
- This package always passes `algorithms=[ALGORITHM]` explicitly to
  `jwt.decode()` (never accepting whatever algorithm the token header
  claims), which is the standard mitigation for JWT "alg: none" and
  algorithm-confusion attacks.
