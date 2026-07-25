# Getting Started

## 1. Install

```bash
pip install drf-jwt-auth-kit
```

## 2. Add the app and configure authentication

```python
# settings.py
INSTALLED_APPS = [
    ...,
    "drf_jwt_auth_kit",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "drf_jwt_auth_kit.authentication.JWTAuthentication",
    ],
}
```

```bash
python manage.py migrate
```

## 3. Wire up the authentication API

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    path("auth/", include("drf_jwt_auth_kit.urls")),
]
```

This gives you: `POST /auth/login/`, `POST /auth/refresh/`, `POST
/auth/logout/`, `POST /auth/logout-all/`, `GET/DELETE /auth/devices/`,
`GET /auth/login-history/`, and `/auth/mfa/totp/*`.

## 4. Log in

```http
POST /auth/login/
Content-Type: application/json

{"username": "ada", "password": "hunter2"}
```

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "device": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "label": "",
    "user_agent": "Mozilla/5.0 ...",
    "created_at": "2026-07-25T10:00:00Z",
    "last_used_at": "2026-07-25T10:00:00Z",
    "is_current": true
  }
}
```

The response also sets two cookies: an httpOnly `refresh_token` cookie
and a JavaScript-readable `refresh_csrftoken` cookie. Store
`access_token` in memory (not `localStorage`) and send it as
`Authorization: Bearer <access_token>` on every authenticated request.

## 5. Refresh before the access token expires

```http
POST /auth/refresh/
X-Refresh-CSRFToken: <value of the refresh_csrftoken cookie>
```

The browser sends the httpOnly `refresh_token` cookie automatically; you
only need to read the `refresh_csrftoken` cookie yourself and echo it
back in the header (see [Examples](examples.md) for real client code).
The response sets fresh cookies and returns a new `access_token`.

## 6. Log out

```http
POST /auth/logout/
X-Refresh-CSRFToken: <value of the refresh_csrftoken cookie>
```

Revokes the current device and clears both cookies. Use `POST
/auth/logout-all/` (with a valid `Authorization: Bearer` header instead)
to log out of every device at once.

See [Quick Start](quickstart.md) for a complete worked example, and
[Examples](examples.md) for SPA and mobile client code.
