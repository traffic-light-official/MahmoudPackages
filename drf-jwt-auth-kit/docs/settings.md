# Settings

All settings live under a single Django setting, `JWT_AUTH_KIT`, a dict
merged on top of the defaults below. Unknown keys and wrong-typed values
raise `django.core.exceptions.ImproperlyConfigured` at first access.

```python
JWT_AUTH_KIT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=10),
}
```

## Reference

### `ACCESS_TOKEN_LIFETIME`

- **Type:** `datetime.timedelta`
- **Default:** `timedelta(minutes=5)`

How long an access token is valid for. Kept short since access tokens
are verified statelessly by default - see `CHECK_DEVICE_REVOCATION_ON_AUTH`.

### `REFRESH_TOKEN_LIFETIME`

- **Type:** `datetime.timedelta`
- **Default:** `timedelta(days=7)`

How long a normal (non-"remember me") refresh token is valid for.

### `REMEMBER_ME_REFRESH_TOKEN_LIFETIME`

- **Type:** `datetime.timedelta`
- **Default:** `timedelta(days=30)`

How long a "remember me" refresh token is valid for.

### `ALGORITHM`

- **Type:** `str`
- **Default:** `"HS256"`

JWT signing algorithm, passed directly to PyJWT. Any algorithm PyJWT
supports works, including asymmetric ones (`RS256`, `ES256`, ...).

### `SIGNING_KEY`

- **Type:** `str | None`
- **Default:** `None`

Key used to sign (and, for symmetric algorithms, verify) tokens. When
`None`, falls back to Django's own `SECRET_KEY`.

### `VERIFYING_KEY`

- **Type:** `str | None`
- **Default:** `None`

Key used only to *verify* tokens, for asymmetric algorithms. When
`None`, `SIGNING_KEY` (or `SECRET_KEY`) is used for both.

### `ISSUER`

- **Type:** `str | None`
- **Default:** `None`

JWT `iss` claim. When `None`, the claim is omitted (and not verified).

### `AUDIENCE`

- **Type:** `str | None`
- **Default:** `None`

JWT `aud` claim (and the value verified against it). When `None`, the
claim is omitted and audience is not checked.

### `REFRESH_COOKIE_NAME`

- **Type:** `str`
- **Default:** `"refresh_token"`

Name of the httpOnly cookie carrying the refresh token.

### `REFRESH_COOKIE_DOMAIN`

- **Type:** `str | None`
- **Default:** `None`

`Domain` attribute of the refresh cookie. `None` scopes the cookie to
the exact host that set it.

### `REFRESH_COOKIE_PATH`

- **Type:** `str`
- **Default:** `"/"`

`Path` attribute of the refresh cookie and the CSRF cookie.

### `REFRESH_COOKIE_SECURE`

- **Type:** `bool`
- **Default:** `True`

`Secure` attribute of the refresh cookie. Only disable for local
development over plain HTTP - never in production.

### `REFRESH_COOKIE_SAMESITE`

- **Type:** `str`
- **Default:** `"Lax"`

One of `"Lax"`, `"Strict"`, or `"None"` (`"None"` requires
`REFRESH_COOKIE_SECURE=True` and is needed for cross-site SPA
deployments).

### `CSRF_COOKIE_NAME`

- **Type:** `str`
- **Default:** `"refresh_csrftoken"`

Name of the (non-httpOnly, JavaScript-readable) double-submit CSRF
cookie paired with the refresh cookie.

### `CSRF_HEADER_NAME`

- **Type:** `str`
- **Default:** `"X-Refresh-CSRFToken"`

Name of the request header a client must echo the CSRF cookie's value
back in for cookie-authenticated refresh/logout requests.

### `BLACKLIST_AFTER_ROTATION`

- **Type:** `bool`
- **Default:** `True`

When `True`, rotating a refresh token also marks the old one revoked in
the database (the basis for reuse detection). Disabling this disables
reuse detection entirely - not recommended.

### `CHECK_DEVICE_REVOCATION_ON_AUTH`

- **Type:** `bool`
- **Default:** `False`

When `True`, `JWTAuthentication` performs one extra database query per
request to confirm the access token's device has not been revoked,
making logout-all take effect immediately instead of only once the
access token naturally expires.

### `MFA_PROVIDER`

- **Type:** `str` (dotted path)
- **Default:** `"drf_jwt_auth_kit.mfa.NullMFAProvider"`

The `MFAProvider` subclass used during login. The built-in alternative
is `"drf_jwt_auth_kit.mfa.TOTPProvider"`.

### `TOTP_ISSUER_NAME`

- **Type:** `str`
- **Default:** `"drf-jwt-auth-kit"`

Issuer name embedded in TOTP provisioning URIs, shown in authenticator
apps next to the account name.

### `TOTP_VALID_WINDOW`

- **Type:** `int`
- **Default:** `1`

Number of 30-second time steps of clock drift to tolerate on either
side when verifying a TOTP code.

### `LOGIN_HISTORY_ENABLED`

- **Type:** `bool`
- **Default:** `True`

When `True`, every login attempt (success or failure) is recorded in
`LoginHistory`.
