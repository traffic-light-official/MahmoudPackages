# Installation

## Requirements

| Dependency | Supported versions |
| --- | --- |
| Python | 3.10, 3.11, 3.12, 3.13 |
| Django | 4.2, 5.0, 5.1, 5.2 |
| Django REST Framework | 3.14+ |
| redis (optional) | 5.0+, only if using `RedisBackend` |

## Standard install

```bash
pip install drf-idempotency
```

## With Redis backend support

```bash
pip install drf-idempotency[redis]
```

`drf_idempotency.backends.redis` raises a clear `ImportError` naming this
extra if you try to use `RedisBackend` without it installed.

## Django project setup

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...,
    "drf_idempotency",
]
```

This is required if you use `DatabaseBackend` (it provides the
`IdempotencyRecord` model — run `python manage.py migrate` after adding
it). It's technically optional if you use `RedisBackend` exclusively, but
harmless to include either way, and required if you want the
`cleanup_expired_idempotency_keys` management command available (Django
only discovers management commands from apps in `INSTALLED_APPS`).

## Verifying the install

```bash
python -c "import drf_idempotency; print(drf_idempotency.__version__)"
```

## Upgrading

Check [CHANGELOG.md](https://github.com/mahmoudgshaker/drf-idempotency/blob/main/CHANGELOG.md)
before upgrading across a major version. If a migration to the
`IdempotencyRecord` model is ever needed for a schema change, it will ship
with the release and be picked up by your next `migrate`.
