# drf-jwt-auth-kit

[![PyPI version](https://img.shields.io/pypi/v/drf-jwt-auth-kit.svg)](https://pypi.org/project/drf-jwt-auth-kit/)
[![Python versions](https://img.shields.io/pypi/pyversions/drf-jwt-auth-kit.svg)](https://pypi.org/project/drf-jwt-auth-kit/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Enterprise JWT authentication for Django REST Framework: short-lived
access tokens, httpOnly-cookie refresh tokens with rotation and reuse
detection, per-device session management, and MFA extension hooks -
everything a production login flow needs, not just token issuance.

## Why

Most JWT packages for DRF stop at "issue an access token and a refresh
token." That leaves an application to build, on its own, the parts that
actually make JWT auth safe to ship: keeping the refresh token out of
JavaScript's reach (httpOnly cookies), detecting a stolen refresh token
being replayed (rotation + reuse detection), letting a user see and
revoke their own logged-in devices, and a place to plug in MFA. This
package provides all of it as one cohesive, tested unit.

## Features

- **Short-lived JWT access tokens** (default 5 minutes), verified
  statelessly - no database hit on every authenticated request.
- **httpOnly, Secure, SameSite refresh cookies** - never readable by
  JavaScript, with a double-submit CSRF token for the refresh/logout
  endpoints that accept them.
- **Refresh token rotation with reuse detection**: every refresh call
  issues a new refresh token and revokes the old one; presenting an
  already-rotated token revokes the *entire token family* immediately,
  the standard signal that a token was stolen.
- **Blacklist support**: revoked/rotated tokens are rejected even if
  their JWT signature and expiry are still valid.
- **Device and session management**: every login is tied to a device
  record; list your own devices, revoke one, or log out everywhere.
- **"Remember me"**: a longer-lived refresh token for logins that opt in.
- **MFA extension hooks**: a pluggable `MFAProvider` interface, with a
  ready-to-use RFC 6238 TOTP implementation included.
- **Login history**: every login attempt (success or failure) is
  recorded with IP, user agent, and device.
- **OpenAPI-friendly** views and serializers; drop straight into a
  `drf-spectacular` schema.
- **Fully typed**, PEP 561 compatible, `mypy --strict` clean.

## Installation

```bash
pip install drf-jwt-auth-kit
```

Requires Python 3.10+, Django 4.2+, and Django REST Framework 3.14+.

## Quick Start

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
from django.urls import include, path

urlpatterns = [
    path("auth/", include("drf_jwt_auth_kit.urls")),
]
```

```bash
python manage.py migrate
```

That's it:

```
POST /auth/login/        {"username": "...", "password": "..."}
POST /auth/refresh/       (reads the httpOnly refresh cookie)
POST /auth/logout/        (revokes the current device, clears the cookie)
POST /auth/logout-all/    (revokes every device)
GET  /auth/devices/       (list your own logged-in devices)
DELETE /auth/devices/<id>/ (revoke one device)
GET  /auth/login-history/
```

See [`docs/quickstart.md`](docs/quickstart.md) for the full request/response
shapes and SPA/mobile client examples.

## Documentation

Full documentation is available at
[Documentation Home Page](https://mahmoudgshake.github.io/MahmoudPackages/drf-jwt-auth-kit/), including:

- [Getting Started](https://mahmoudgshake.github.io/MahmoudPackages/drf-jwt-auth-kit/getting-started)
- [Installation](https://mahmoudgshake.github.io/MahmoudPackages/drf-jwt-auth-kit/installation)
- [Configuration](https://mahmoudgshake.github.io/MahmoudPackages/drf-jwt-auth-kit/configuration) / [Settings](https://mahmoudgshake.github.io/MahmoudPackages/drf-jwt-auth-kit/settings)
- [Quick Start](https://mahmoudgshake.github.io/MahmoudPackages/drf-jwt-auth-kit/quickstart)
- [Advanced Usage](https://mahmoudgshake.github.io/MahmoudPackages/drf-jwt-auth-kit/advanced-usage)
- [Architecture](https://mahmoudgshake.github.io/MahmoudPackages/drf-jwt-auth-kit/architecture)
- [API Reference](https://mahmoudgshake.github.io/MahmoudPackages/drf-jwt-auth-kit/api-reference)
- [Examples](https://mahmoudgshake.github.io/MahmoudPackages/drf-jwt-auth-kit/examples)
- [Common Patterns](https://mahmoudgshake.github.io/MahmoudPackages/drf-jwt-auth-kit/common-patterns)
- [Performance](https://mahmoudgshake.github.io/MahmoudPackages/drf-jwt-auth-kit/performance)
- [Security](https://mahmoudgshake.github.io/MahmoudPackages/drf-jwt-auth-kit/security)
- [Testing](https://mahmoudgshake.github.io/MahmoudPackages/drf-jwt-auth-kit/testing)
- [Deployment](https://mahmoudgshake.github.io/MahmoudPackages/drf-jwt-auth-kit/deployment)
- [FAQ](https://mahmoudgshake.github.io/MahmoudPackages/drf-jwt-auth-kit/faq)
- [Troubleshooting](https://mahmoudgshake.github.io/MahmoudPackages/drf-jwt-auth-kit/troubleshooting)

## Contributing

Contributions are welcome — see [Contributing](https://mahmoudgshake.github.io/MahmoudPackages/drf-jwt-auth-kit/contributing).

## License

MIT — see [LICENSE](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-jwt-auth-kit/LICENSE).
