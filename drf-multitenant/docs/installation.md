# Installation

## Requirements

- Python 3.10, 3.11, 3.12, or 3.13
- Django 4.2, 5.0, 5.1, or 5.2
- Django REST Framework 3.14+

## Install from PyPI

```bash
pip install drf-multitenant
```

No optional extras — `django` and `djangorestframework` are the only
runtime dependencies. There is no Redis, cache backend, or database
driver dependency: per-tenant caching (`drf_multitenant.cache`) sits on
top of whatever `CACHES` backend your project already configures.

## Enable it in your project

```python
# settings.py
MIDDLEWARE = [
    ...,
    "drf_multitenant.middleware.TenantMiddleware",
]
MULTITENANT = {
    "TENANT_MODEL": "accounts.Tenant",
}
```

`drf_multitenant` itself is **not** a Django app — it defines no models
or migrations of its own (`TenantScopedModel` is an abstract base your
own concrete models inherit from), so it does not need to appear in
`INSTALLED_APPS`.

## Verify the install

```bash
python -c "import drf_multitenant; print(drf_multitenant.__version__)"
```

## Development install

```bash
git clone https://github.com/mahmoudgshaker/drf-multitenant.git
cd drf-multitenant
pip install -e ".[dev]"
```

The `dev` extra pulls in `test` (pytest, pytest-django, coverage,
hypothesis) and `docs` (mkdocs, mkdocs-material, mkdocstrings), plus
ruff, black, mypy, and the django/drf type stubs. See
[Contributing](contributing.md) for the full workflow.
