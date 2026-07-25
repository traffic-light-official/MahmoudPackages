# Installation

```bash
pip install drf-n-plus-one-query-guard
```

Requires Python 3.10+, Django 4.2-5.2, and Django REST Framework 3.14+.

## Django project setup

```python
# settings.py
INSTALLED_APPS = [
    ...,
    "drf_n_plus_one_query_guard",
]
```

Required for the `N_PLUS_ONE_GUARD` setting to be validated on app load
(see [Settings](settings.md)) - even if you only ever use
`assert_no_n_plus_one()` in tests, which itself needs no Django setting
at all (see [Testing](testing.md)).

No migrations to run - this package defines no models.

## Optional: guard every request

```python
# settings.py
MIDDLEWARE = [
    ...,
    "drf_n_plus_one_query_guard.middleware.NPlusOneGuardMiddleware",
]
```

Only add this if you want request-level guarding (a `DEBUG`-only
response header, or - opt-in - a hard failure) - see
[Advanced Usage](advanced-usage.md#middleware). Not required for
`assert_no_n_plus_one()` or `guard_view()`.

## Verifying the install

```python
>>> import drf_n_plus_one_query_guard
>>> drf_n_plus_one_query_guard.__version__
'1.0.0'
```
