# Installation

```bash
pip install drf-bulk-operations
```

Requires Python 3.10+, Django 4.2-5.2, and Django REST Framework 3.14+.

## Django project setup

```python
# settings.py
INSTALLED_APPS = [
    ...,
    "drf_bulk_operations",
]
```

Registering the app is for consistency with this workspace's other
packages only - `drf_bulk_operations` defines no models and needs no
app-loading side effects of its own, so there's nothing to migrate.

## No extra dependencies

This package's only runtime dependencies are Django and Django REST
Framework themselves - it uses Django's own `transaction.atomic()` and
DRF's own serializer/permission machinery directly, nothing else.

## Verifying the install

```python
>>> import drf_bulk_operations
>>> drf_bulk_operations.__version__
'1.0.0'
```
