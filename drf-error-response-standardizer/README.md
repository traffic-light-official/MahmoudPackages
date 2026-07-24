# drf-error-response-standardizer

[![PyPI version](https://img.shields.io/pypi/v/drf-error-response-standardizer.svg)](https://pypi.org/project/drf-error-response-standardizer/)
[![Python versions](https://img.shields.io/pypi/pyversions/drf-error-response-standardizer.svg)](https://pypi.org/project/drf-error-response-standardizer/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[RFC 9457 Problem Details](https://www.rfc-editor.org/rfc/rfc9457.html) for
Django REST Framework — a drop-in `EXCEPTION_HANDLER` that turns every error
response (validation, permissions, throttling, your own domain exceptions,
even uncaught bugs) into a consistent, machine-readable, frontend-friendly
JSON shape.

```
POST /api/articles/
```

```json
{
  "type": "https://api.example.com/problems/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "One or more fields failed validation.",
  "instance": "/api/articles/",
  "code": "validation_error",
  "errors": [
    { "pointer": "title", "detail": "This field is required.", "code": "required" },
    { "pointer": "author/email", "detail": "Enter a valid email address.", "code": "invalid" }
  ],
  "correlation_id": "8f14e45f-ceea-4b4c-9c6c-7b3e0f2a5c1a",
  "request_id": "3f2504e0-4f89-11d3-9a0c-0305e82c3301",
  "timestamp": "2026-07-25T10:15:30.123456+00:00"
}
```

## Why

DRF's default exception handler returns three different, inconsistent
shapes depending on what went wrong (`{"detail": "..."}`, a bag of
field-name keys, or nothing at all for uncaught exceptions), gives
frontend/mobile clients nothing to branch on but English prose, and has no
concept of correlation IDs, localization, or an error catalog. This package
replaces it with a single, RFC-compliant shape and the machinery
(registry, normalization, catalog, OpenAPI integration) needed to keep
every error response - built-in or custom - consistent as an API grows.

## Features

- **RFC 9457 compliant**: `type`, `title`, `status`, `detail`, `instance`,
  plus extension members, served as `application/problem+json`.
- **Nested validation error normalization**: deeply nested serializer
  errors (including `many=True` and `ListField`) flattened into a flat
  `errors` array with JSON-Pointer-style paths.
- **Machine-readable `code`** on every response, and a **catalog
  generator** (`generate_error_catalog` management command) so error
  documentation never drifts from what the API actually returns.
- **Extensible registry**: map your own exception classes to a problem
  type in one line, or raise `ProblemAPIException` directly for full
  control.
- **Correlation IDs, request IDs, and W3C trace IDs**, propagated by
  `CorrelationIdMiddleware` on every request, not just errors.
- **Localization** of titles/details via Django's standard
  `Accept-Language` negotiation, no `LocaleMiddleware` required.
- **OpenAPI integration** for `drf-spectacular`: registers the
  `ProblemDetail` schema and default error responses automatically.
- **Preserves DRF's own header semantics**: `WWW-Authenticate` on 401s,
  `Retry-After` on 429s, and transaction rollback under
  `ATOMIC_REQUESTS`.
- **`drf-standardized-errors` migration path** via the
  `STANDARDIZED_ERRORS_COMPAT` setting.
- **Fully typed**, PEP 561 compatible, `mypy --strict` clean.

## Installation

```bash
pip install drf-error-response-standardizer

# with OpenAPI schema support
pip install drf-error-response-standardizer[openapi]
```

Requires Python 3.10+, Django 4.2+, and Django REST Framework 3.14+.

## Quick Start

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

That's it — every DRF exception (validation, `NotFound`, `PermissionDenied`,
`Throttled`, ...) now returns an RFC 9457 body. To add your own:

```python
from drf_error_response_standardizer.exceptions import ConflictError


def ship_order(order):
    if order.shipped:
        raise ConflictError("Order has already shipped.", extensions={"order_id": order.id})
```

Or register a mapping for an existing exception class without changing
where it's raised:

```python
from drf_error_response_standardizer.codes import ErrorType
from drf_error_response_standardizer.registry import register

register(
    OutOfStockError,
    ErrorType(code="out_of_stock", title="Item Out of Stock", slug="out-of-stock", status=409),
)
```

See [`docs/quickstart.md`](docs/quickstart.md) and
[`docs/advanced-usage.md`](docs/advanced-usage.md) for localization, the
error catalog, and OpenAPI integration.

## Documentation

Full documentation is available at
[Documentation Home Page](https://mahmoudgshake.github.io/MahmoudPackages/drf-error-response-standardizer/), including:

- [Getting Started](https://mahmoudgshake.github.io/MahmoudPackages/drf-error-response-standardizer/getting-started)
- [Installation](https://mahmoudgshake.github.io/MahmoudPackages/drf-error-response-standardizer/installation)
- [Configuration](https://mahmoudgshake.github.io/MahmoudPackages/drf-error-response-standardizer/configuration) / [Settings](https://mahmoudgshake.github.io/MahmoudPackages/drf-error-response-standardizer/settings)
- [Quick Start](https://mahmoudgshake.github.io/MahmoudPackages/drf-error-response-standardizer/quickstart)
- [Advanced Usage](https://mahmoudgshake.github.io/MahmoudPackages/drf-error-response-standardizer/advanced-usage)
- [Architecture](https://mahmoudgshake.github.io/MahmoudPackages/drf-error-response-standardizer/architecture)
- [API Reference](https://mahmoudgshake.github.io/MahmoudPackages/drf-error-response-standardizer/api-reference)
- [Examples](https://mahmoudgshake.github.io/MahmoudPackages/drf-error-response-standardizer/examples)
- [Common Patterns](https://mahmoudgshake.github.io/MahmoudPackages/drf-error-response-standardizer/common-patterns)
- [Performance](https://mahmoudgshake.github.io/MahmoudPackages/drf-error-response-standardizer/performance)
- [Security](https://mahmoudgshake.github.io/MahmoudPackages/drf-error-response-standardizer/security)
- [Testing](https://mahmoudgshake.github.io/MahmoudPackages/drf-error-response-standardizer/testing)
- [Deployment](https://mahmoudgshake.github.io/MahmoudPackages/drf-error-response-standardizer/deployment)
- [FAQ](https://mahmoudgshake.github.io/MahmoudPackages/drf-error-response-standardizer/faq)
- [Troubleshooting](https://mahmoudgshake.github.io/MahmoudPackages/drf-error-response-standardizer/troubleshooting)

## Contributing

Contributions are welcome — see [Contributing](https://mahmoudgshake.github.io/MahmoudPackages/drf-error-response-standardizer/contributing).

## License

MIT — see [LICENSE](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-error-response-standardizer/LICENSE).
