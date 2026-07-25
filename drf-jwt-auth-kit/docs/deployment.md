# Deployment

## Checklist

- [ ] `drf_jwt_auth_kit` in `INSTALLED_APPS`, migrations applied.
- [ ] `REFRESH_COOKIE_SECURE` is `True` (the default) - served over HTTPS.
- [ ] `REFRESH_COOKIE_SAMESITE` matches your deployment topology: `"Lax"`
      for same-site, `"None"` (with `Secure=True`) for a cross-site SPA.
- [ ] A dedicated `SIGNING_KEY` set if you want to rotate JWT signing
      independently of Django's `SECRET_KEY`.
- [ ] A scheduler (cron, Celery beat, etc.) configured to run `python
      manage.py cleanup_expired_tokens` periodically.
- [ ] If MFA is enabled, `TOTP_ISSUER_NAME` set to your actual product
      name (shown in users' authenticator apps).
- [ ] Reverse proxy/load balancer forwards `X-Forwarded-For` correctly if
      you rely on `LoginHistory.ip_address` - see
      [Security](security.md#login-history-and-ip-addresses).

## Scheduling cleanup

```cron
0 3 * * * cd /app && python manage.py cleanup_expired_tokens
```

Safe to run at any cadence; it only deletes rows that expired more than
a day ago; it never touches active tokens.

## Key rotation

To rotate `SIGNING_KEY` without invalidating every existing session
immediately, accept both the old and new key temporarily by decoding
with the new key first and falling back to the old one on
`InvalidTokenError`, or simply accept that a full key rotation forces
re-login (issue everyone a fresh token pair) - the simpler and more
common approach given `ACCESS_TOKEN_LIFETIME` is short and
`REFRESH_TOKEN_LIFETIME` up to 30 days is not so long that a scheduled
forced re-login is disruptive.

## Multi-instance deployments

Nothing in this package requires sticky sessions or shared in-memory
state: `Device`/`RefreshToken`/`LoginHistory` all live in the database,
and access token verification only needs the shared `SIGNING_KEY`/`SECRET_KEY`
(the same requirement any multi-instance Django deployment already has).

## Cross-site SPA deployments

See [Configuration](configuration.md#cross-site-spa-on-a-different-domain-deployments)
for the `REFRESH_COOKIE_SAMESITE`/`REFRESH_COOKIE_DOMAIN` settings
needed, and ensure your CORS configuration
(`django-cors-headers` or equivalent) allows credentialed requests
(`Access-Control-Allow-Credentials: true`) from your frontend's origin
specifically (not `*`, which is incompatible with credentialed requests).

## Zero-downtime rollout

Adding `drf-jwt-auth-kit` to an existing project is additive: new
tables, new URLs (only if you `include()` them), and a new
authentication class you opt into via
`DEFAULT_AUTHENTICATION_CLASSES`. If you are migrating *from* another
JWT package, run both authentication classes side by side during a
transition window (`DEFAULT_AUTHENTICATION_CLASSES` accepts a list, tried
in order) rather than a hard cutover, so already-issued tokens from the
old system keep working until they expire.
