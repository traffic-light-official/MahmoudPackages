# Installation

## Requirements

- Python 3.10, 3.11, 3.12, or 3.13
- Django 4.2, 5.0, 5.1, or 5.2
- Django REST Framework 3.14+

## Base install

```bash
pip install drf-error-response-standardizer
```

## Optional extras

```bash
# OpenAPI schema integration (drf-spectacular)
pip install drf-error-response-standardizer[openapi]
```

## Enable the management command (optional)

The `generate_error_catalog` management command (see
[Common Patterns](common-patterns.md#generating-the-error-catalog-in-ci))
requires the package to be a registered Django app:

```python
# settings.py
INSTALLED_APPS = [
    ...,
    "drf_error_response_standardizer",
]
```

Everything else - the exception handler, middleware, registry, and
normalization functions - works without adding the app to
`INSTALLED_APPS`.

## Verifying the install

```bash
python -c "import drf_error_response_standardizer; print(drf_error_response_standardizer.__version__)"
```

## Next steps

Continue to [Configuration](configuration.md) to wire the exception
handler and middleware into your project, or [Settings](settings.md) for
the full list of configuration options.
