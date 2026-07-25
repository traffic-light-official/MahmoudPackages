# drf-jwt-auth-kit

Enterprise JWT authentication for Django REST Framework: short-lived
access tokens, httpOnly-cookie refresh tokens with rotation and reuse
detection, per-device session management, and MFA extension hooks.

```python
from drf_jwt_auth_kit.devices import create_device
from drf_jwt_auth_kit.rotation import issue_token_pair

device = create_device(user=user, request=request)
pair = issue_token_pair(user=user, device=device)
```

Most projects never call these directly, though - `POST /auth/login/`
(from the ready-to-`include()` `drf_jwt_auth_kit.urls`) does this for you.

## Why this exists

Most JWT packages for DRF stop at "issue an access token and a refresh
token." That leaves an application to build, on its own, the parts that
actually make JWT auth safe to ship in production:

1. **Keep the refresh token out of JavaScript's reach** - an httpOnly
   cookie, not `localStorage`.
2. **Detect a stolen refresh token being replayed** - rotation with
   reuse detection, the same technique Auth0 and Google use.
3. **Let a user see and revoke their own logged-in devices** - "what's
   signed into my account" is a baseline expectation now.
4. **Have a place to plug in MFA** - without forcing one specific
   second factor on every project.

`drf-jwt-auth-kit` provides all of it as one cohesive, tested unit.

## Where to go next

- New to the package? Start with [Getting Started](getting-started.md).
- Wiring it into an existing project? See [Installation](installation.md)
  and [Configuration](configuration.md).
- Want the full picture of how it works? Read [Architecture](architecture.md).
- Looking for a specific class or setting? Jump to
  [API Reference](api-reference.md) or [Settings](settings.md).
- Building an SPA or mobile client? See [Examples](examples.md).
- Something not behaving as expected? Check [Troubleshooting](troubleshooting.md)
  and the [FAQ](faq.md).

## At a glance

| Task | Where |
| --- | --- |
| Authenticate API requests | [`JWTAuthentication`](api-reference.md#jwtauthentication) |
| Log a user in | [`LoginView`](api-reference.md#loginview) / `POST /auth/login/` |
| Refresh a session | [`RefreshView`](api-reference.md#refreshview) / `POST /auth/refresh/` |
| Log out one device / everywhere | `POST /auth/logout/` / `POST /auth/logout-all/` |
| List/revoke devices | [`DeviceViewSet`](api-reference.md#deviceviewset) |
| Add MFA | [`MFAProvider`](api-reference.md#mfaprovider) / [TOTP](advanced-usage.md#mfa-with-totp) |
| Change lifetimes, cookies, algorithm | [Settings](settings.md) |
