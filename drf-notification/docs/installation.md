# Installation

## Requirements

- Python 3.10, 3.11, 3.12, or 3.13
- Django 4.2, 5.0, 5.1, or 5.2
- Django REST Framework 3.14+

## Base install

```bash
pip install drf-notification
```

## Optional extras

```bash
# Celery-backed asynchronous delivery and retry
pip install drf-notification[celery]

# OpenAPI schema integration (drf-spectacular) - no dedicated schema
# customization is needed since every view uses standard DRF serializers,
# but installing drf-spectacular alongside this package works out of the box
pip install drf-spectacular
```

## Enable the app

```python
# settings.py
INSTALLED_APPS = [
    ...,
    "drf_notification",
]
```

```bash
python manage.py migrate
```

## Verifying the install

```bash
python -c "import drf_notification; print(drf_notification.__version__)"
python manage.py showmigrations drf_notification
```

## Next steps

Continue to [Configuration](configuration.md) to register event types
and wire up the preference-center API, or [Settings](settings.md) for
the full list of configuration options.
