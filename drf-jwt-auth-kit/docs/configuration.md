# Configuration

## Minimal configuration

```python
# settings.py
INSTALLED_APPS = [..., "drf_jwt_auth_kit"]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "drf_jwt_auth_kit.authentication.JWTAuthentication",
    ],
}
```

```python
# urls.py
urlpatterns = [path("auth/", include("drf_jwt_auth_kit.urls"))]
```

Everything below is optional refinement.

## Package settings

Every behavioral option lives under one Django setting, `JWT_AUTH_KIT`:

```python
JWT_AUTH_KIT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=10),
    "REFRESH_COOKIE_SAMESITE": "None",  # cross-site SPA deployment
}
```

See [Settings](settings.md) for the full list.

## Cross-site (SPA on a different domain) deployments

If your frontend and API are on different origins (e.g.
`app.example.com` and `api.example.com`), the refresh cookie needs
`SameSite=None` (which requires `Secure=True`, always the case in
production):

```python
JWT_AUTH_KIT = {
    "REFRESH_COOKIE_SAMESITE": "None",
    "REFRESH_COOKIE_DOMAIN": ".example.com",
}
```

Your frontend's `fetch`/`axios` calls must also include
`credentials: "include"` - see [Examples](examples.md#spa-javascript-client).

## MFA

```python
JWT_AUTH_KIT = {
    "MFA_PROVIDER": "drf_jwt_auth_kit.mfa.TOTPProvider",
}
```

MFA is per-user opt-in: `TOTPProvider.is_required()` only returns `True`
for users with a *confirmed* `TOTPDevice` row, created via `POST
/auth/mfa/totp/setup/` + `/confirm/`. See
[Advanced Usage](advanced-usage.md#mfa-with-totp).

## Immediate revocation (optional, has a cost)

By default, `logout-all` takes effect on *new* logins/refreshes
immediately, but an already-issued access token keeps working until it
naturally expires (this is the standard, intentional JWT trade-off - see
[Architecture](architecture.md)). To force immediate revocation at the
cost of one extra database query per authenticated request:

```python
JWT_AUTH_KIT = {"CHECK_DEVICE_REVOCATION_ON_AUTH": True}
```

## Asymmetric signing (RS256, etc.)

```python
JWT_AUTH_KIT = {
    "ALGORITHM": "RS256",
    "SIGNING_KEY": PRIVATE_KEY_PEM,
    "VERIFYING_KEY": PUBLIC_KEY_PEM,
}
```

Useful when a separate service needs to verify tokens without holding
the ability to mint them.

## OpenAPI

No custom integration is needed: every view is a standard DRF
`APIView`/`ViewSet` with serializers, so `drf-spectacular`'s automatic
schema generation covers the whole API without additional configuration.
