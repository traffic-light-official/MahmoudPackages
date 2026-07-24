# Getting Started

This page gets a fresh project from zero to standardized error responses
in about two minutes.

## 1. Install

```bash
pip install drf-error-response-standardizer
```

## 2. Wire up the exception handler

```python
# settings.py
REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": (
        "drf_error_response_standardizer.handler.problem_details_exception_handler"
    ),
}
```

Every exception DRF already knows how to handle - `ValidationError`,
`NotFound`, `PermissionDenied`, `NotAuthenticated`, `Throttled`, and so on -
now returns an RFC 9457 body instead of DRF's default shape.

## 3. Add the correlation ID middleware

```python
# settings.py
MIDDLEWARE = [
    "drf_error_response_standardizer.middleware.CorrelationIdMiddleware",
    # ... the rest of your middleware ...
]
```

Put it near the top of the list so the IDs it assigns are available to
every downstream middleware, view, and log line. Every response - success
or error - now carries `X-Correlation-ID` and `X-Request-ID` headers, and
error responses include them as `correlation_id`/`request_id` extension
members too.

## 4. Try it

```pycon
>>> from rest_framework.test import APIClient
>>> client = APIClient()
>>> response = client.post("/api/articles/", {"body": "missing a title"}, format="json")
>>> response.status_code
400
>>> response.data["errors"]
[{'pointer': 'title', 'detail': 'This field is required.', 'code': 'required'}]
```

## 5. Raise your own problems

For domain errors that do not map to an existing DRF exception, either
raise a ready-made subclass:

```python
from drf_error_response_standardizer.exceptions import ConflictError

raise ConflictError("Order has already shipped.", extensions={"order_id": order.id})
```

or register a mapping for an exception class you already raise elsewhere
in the codebase, without touching the call site:

```python
from drf_error_response_standardizer.codes import ErrorType
from drf_error_response_standardizer.registry import register

register(
    OutOfStockError,
    ErrorType(code="out_of_stock", title="Item Out of Stock", slug="out-of-stock", status=409),
)
```

See [Quick Start](quickstart.md) for a complete worked example, and
[Advanced Usage](advanced-usage.md) for localization, the error catalog,
and OpenAPI integration.
