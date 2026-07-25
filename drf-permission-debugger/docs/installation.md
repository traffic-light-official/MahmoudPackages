# Installation

```bash
pip install drf-permission-debugger
```

Requires Python 3.10+, Django 4.2-5.2, and Django REST Framework 3.14+.

## Django project setup

```python
# settings.py
INSTALLED_APPS = [
    ...,
    "drf_permission_debugger",
]
```

Registering the app is required for Django to discover the
`show_view_permissions` management command - this package defines no
models, so there's nothing to migrate.

## No extra dependencies

This package's only runtime dependencies are Django and Django REST
Framework themselves - it only calls their own existing permission,
request, and response APIs.

## Verifying the install

```python
>>> import drf_permission_debugger
>>> drf_permission_debugger.__version__
'1.0.0'
```
