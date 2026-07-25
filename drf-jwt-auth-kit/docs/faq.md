# FAQ

## Why does logout-all not immediately kill an already-issued access token?

By design - see
[Architecture](architecture.md#stateless-access-tokens-by-design). Access
tokens are verified statelessly for performance; `ACCESS_TOKEN_LIFETIME`
(5 minutes by default) bounds how long a revoked device's access token
keeps working. Enable `CHECK_DEVICE_REVOCATION_ON_AUTH` if you need
immediate revocation and can accept one extra query per request.

## Why is the refresh token in a cookie instead of the response body?

So JavaScript never has direct access to it, even under a successful XSS
attack - see [Security](security.md#refresh-tokens-are-httponly-by-design).
If your client genuinely cannot use cookies (a subset of native mobile
setups), see [Examples](examples.md#mobile-client-no-cookie-jar) for a
header-based alternative you can add on top of
`drf_jwt_auth_kit.rotation` directly.

## What happens if a refresh token is used twice?

The second use is rejected with `TokenReuseDetectedError`/401, and the
*entire device* (every refresh token belonging to it) is revoked - see
[Architecture](architecture.md#reuse-detection-revokes-the-whole-device-not-just-the-reused-token).

## Can I disable reuse detection?

Yes, via `BLACKLIST_AFTER_ROTATION = False`, but this is not recommended
- see [Advanced Usage](advanced-usage.md#tuning-reuse-detection).

## Do I need Redis or Celery?

No. Everything in this package uses the database and Django's own cache
framework is not required at all. There is no Celery dependency.

## How is a "device" different from a "session"?

They aren't, in this package - one `Device` row is created per login
and represents both. See
[Architecture](architecture.md#a-device-is-both-a-device-and-a-session).

## Can I use a custom user model?

Yes - every FK in this package targets `settings.AUTH_USER_MODEL`. The
only requirement is that `get_user_model().USERNAME_FIELD` and Django's
own `authenticate()` work as normal for your user model, which they do
for any properly configured custom user model.

## Does this package support social login (Google, GitHub, etc.)?

Not directly - `LoginView` is built around Django's own
username/password `authenticate()`. If you already have a social-login
flow that resolves to a Django user, call
`drf_jwt_auth_kit.devices.create_device` and
`drf_jwt_auth_kit.rotation.issue_token_pair` yourself at the end of it -
see [Advanced Usage](advanced-usage.md#building-your-own-login-view).

## How do I support more than one MFA factor at once (e.g. TOTP or SMS)?

Write an `MFAProvider` that composes multiple factors internally (e.g.
try TOTP first, fall back to SMS) - the interface is intentionally just
two methods (`is_required`, `verify`), so this composition is entirely
up to your implementation. See
[Advanced Usage](advanced-usage.md#custom-mfa-providers).

## Why 6-digit TOTP codes instead of 8?

6 digits is what virtually every authenticator app (Google
Authenticator, Authy, 1Password, etc.) defaults to and expects; RFC 6238
supports either, but 8-digit codes are rare in practice and would
surprise users copying a code from their app.
