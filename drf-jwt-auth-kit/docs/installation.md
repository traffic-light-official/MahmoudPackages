# Installation

## Requirements

- Python 3.10, 3.11, 3.12, or 3.13
- Django 4.2, 5.0, 5.1, or 5.2
- Django REST Framework 3.14+
- [PyJWT](https://pyjwt.readthedocs.io/) 2.8+ (installed automatically)

## Base install

```bash
pip install drf-jwt-auth-kit
```

## Enable the app

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

## Verifying the install

```bash
python -c "import drf_jwt_auth_kit; print(drf_jwt_auth_kit.__version__)"
python manage.py showmigrations drf_jwt_auth_kit
```

## Production checklist before going live

- `REFRESH_COOKIE_SECURE` must be `True` (the default) in production -
  only disable it for local development over plain HTTP.
- Set a dedicated `SIGNING_KEY` (distinct from Django's `SECRET_KEY`) if
  you want to be able to rotate JWT signing independently.
- Schedule `python manage.py cleanup_expired_tokens` to run periodically
  (see [Deployment](deployment.md)).

## Next steps

Continue to [Configuration](configuration.md) to wire up the
authentication API, or [Settings](settings.md) for the full list of
configuration options.
