# Configuration

## Minimal configuration

```python
# settings.py
MIDDLEWARE = [
    "drf_error_response_standardizer.middleware.CorrelationIdMiddleware",
    # ... the rest of your middleware ...
]

REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": (
        "drf_error_response_standardizer.handler.problem_details_exception_handler"
    ),
}
```

This alone standardizes every DRF-raised exception. Everything below is
optional refinement.

## Package settings

Every behavioral option lives under one Django setting,
`ERROR_RESPONSE_STANDARDIZER`:

```python
# settings.py
ERROR_RESPONSE_STANDARDIZER = {
    "TYPE_BASE_URI": "https://api.example.com/problems/",
    "MEDIA_TYPE": "application/problem+json",
    "INCLUDE_TIMESTAMP": True,
}
```

See [Settings](settings.md) for the full, documented list.

## OpenAPI (drf-spectacular)

```python
# settings.py
SPECTACULAR_SETTINGS = {
    "POSTPROCESSING_HOOKS": [
        "drf_error_response_standardizer.openapi.problem_details_postprocessing_hook",
    ],
}
```

Registers a `ProblemDetail` OpenAPI component and default error responses
for every operation. See [Advanced Usage](advanced-usage.md#openapi-integration).

## Localization

No extra configuration is required beyond Django's own `LANGUAGES` /
`USE_I18N` settings - `translate()` and `activate_for_request()` use
Django's standard `Accept-Language` negotiation directly, even on
API-only projects that do not install `LocaleMiddleware`. See
[Advanced Usage](advanced-usage.md#localization).

## Custom exception mapping

Register your own exception classes at import time, typically in your
app's `AppConfig.ready()`:

```python
# myapp/apps.py
from django.apps import AppConfig


class MyAppConfig(AppConfig):
    name = "myapp"

    def ready(self) -> None:
        from drf_error_response_standardizer.codes import ErrorType
        from drf_error_response_standardizer.registry import register
        from myapp.exceptions import OutOfStockError

        register(
            OutOfStockError,
            ErrorType(code="out_of_stock", title="Item Out of Stock", slug="out-of-stock", status=409),
        )
```

See [Advanced Usage](advanced-usage.md#custom-exception-mapping) for the
full range of options, including custom builder functions.

## drf-standardized-errors migration

If you are migrating from `drf-standardized-errors` and need its response
shape available during a transition period:

```python
ERROR_RESPONSE_STANDARDIZER = {
    "STANDARDIZED_ERRORS_COMPAT": True,
}
```

This adds a `standardized_errors` extension member alongside the primary
RFC 9457 body; see [FAQ](faq.md#migrating-from-drf-standardized-errors).
