# Getting Started

## Prerequisites

Python 3.10+, Django 4.2+, Django REST Framework 3.14+.

## 1. Install

```bash
pip install drf-idempotency
```

If you plan to use the Redis backend:

```bash
pip install drf-idempotency[redis]
```

## 2. Add the app and choose a backend

```python
# settings.py
INSTALLED_APPS = [
    ...,
    "drf_idempotency",  # required for the database backend's model
]

IDEMPOTENCY = {
    "BACKEND": "drf_idempotency.backends.database.DatabaseBackend",
}
```

```bash
python manage.py migrate
```

(If you use the Redis backend exclusively, `INSTALLED_APPS` isn't
strictly required, but there's no harm leaving it in — see
[Configuration](configuration.md).)

## 3. Apply it — project-wide or per-view

**Project-wide**, via middleware:

```python
MIDDLEWARE = [
    ...,
    "drf_idempotency.middleware.IdempotencyMiddleware",
]
```

**Per-view**, via decorator:

```python
from rest_framework.decorators import api_view
from drf_idempotency import idempotent


@api_view(["POST"])
@idempotent()
def create_payment(request):
    ...
```

Use one or the other for a given view — see
[Troubleshooting](troubleshooting.md) if you need both active
simultaneously in some parts of your project (it's handled safely, but
worth understanding why).

## 4. Try it

```bash
curl -X POST http://localhost:8000/payments/ \
  -H "Idempotency-Key: 6f7a1e3e-2c9d-4b1a-9d0a-6a6f2b6b9b3a" \
  -H "Content-Type: application/json" \
  -d '{"amount": 2000, "currency": "usd"}'
```

Run the exact same command again — you get the identical `201 Created`
response, with `Idempotent-Replayed: true` this time, and no second
payment was created.

## Next steps

- [Configuration](configuration.md) — choosing and tuning a backend.
- [Quick Start](quickstart.md) — key reuse detection, status tracking,
  cleanup.
- [Security](security.md) — read before exposing this on a public API.
