# Quick Start

A complete worked example: a project with TOTP-based MFA and a "remember
me" login option.

## Settings

```python
# settings.py
INSTALLED_APPS = [..., "drf_jwt_auth_kit"]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "drf_jwt_auth_kit.authentication.JWTAuthentication",
    ],
}

JWT_AUTH_KIT = {
    "MFA_PROVIDER": "drf_jwt_auth_kit.mfa.TOTPProvider",
}
```

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    path("auth/", include("drf_jwt_auth_kit.urls")),
]
```

## Enrolling in MFA

```http
POST /auth/mfa/totp/setup/
Authorization: Bearer <access_token>
```

```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "provisioning_uri": "otpauth://totp/drf-jwt-auth-kit:ada?secret=JBSWY3DPEHPK3PXP&issuer=drf-jwt-auth-kit&algorithm=SHA1&digits=6&period=30"
}
```

Render `provisioning_uri` as a QR code (any client-side QR library) for
the user to scan with Google Authenticator, 1Password, etc. Then confirm
with the first generated code:

```http
POST /auth/mfa/totp/confirm/
Authorization: Bearer <access_token>
Content-Type: application/json

{"code": "123456"}
```

## Logging in with MFA and "remember me"

Without a code, once MFA is enabled:

```http
POST /auth/login/
Content-Type: application/json

{"username": "ada", "password": "hunter2"}
```

```json
{"mfa_required": true}
```

With the code and `remember_me`:

```http
POST /auth/login/
Content-Type: application/json

{"username": "ada", "password": "hunter2", "mfa_code": "123456", "remember_me": true}
```

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "device": {"id": "...", "label": "", "is_current": true, "...": "..."}
}
```

The refresh cookie is now valid for `REMEMBER_ME_REFRESH_TOKEN_LIFETIME`
(30 days by default) instead of the normal 7.

## Managing devices

```http
GET /auth/devices/
Authorization: Bearer <access_token>
```

```json
[
  {"id": "3fa8...", "label": "Chrome on macOS", "is_current": true, "...": "..."},
  {"id": "9c1a...", "label": "iPhone 15", "is_current": false, "...": "..."}
]
```

```http
DELETE /auth/devices/9c1a.../
Authorization: Bearer <access_token>
```

Revokes that one device without affecting the current session. Use
`POST /auth/logout-all/` to revoke every device, including the current
one.

## Reviewing login history

```http
GET /auth/login-history/
Authorization: Bearer <access_token>
```

```json
[
  {"username_attempted": "ada", "success": true, "ip_address": "203.0.113.5", "...": "..."},
  {"username_attempted": "ada", "success": false, "failure_reason": "invalid_mfa_code", "...": "..."}
]
```

See [Advanced Usage](advanced-usage.md) for custom MFA providers,
asymmetric signing, and reuse-detection tuning.
