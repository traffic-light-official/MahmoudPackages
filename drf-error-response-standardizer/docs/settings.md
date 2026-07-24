# Settings

All settings live under a single Django setting, `ERROR_RESPONSE_STANDARDIZER`,
a dict merged on top of the defaults below. Unknown keys and wrong-typed
values raise `django.core.exceptions.ImproperlyConfigured` at first access
(not at import time), so a typo surfaces the first time a request actually
hits the exception handler.

```python
ERROR_RESPONSE_STANDARDIZER = {
    "TYPE_BASE_URI": "https://api.example.com/problems/",
}
```

## Reference

### `TYPE_BASE_URI`

- **Type:** `str | None`
- **Default:** `None`

Base URI prepended to relative problem type slugs, e.g.
`"https://api.example.com/problems/"` + `"out-of-stock"` ->
`"https://api.example.com/problems/out-of-stock"`. Must end with a
trailing `/` if set. When `None`, the `type` member is always
`"about:blank"`.

### `MEDIA_TYPE`

- **Type:** `str | None`
- **Default:** `"application/problem+json"`

Value written to the `Content-Type` header of every error response. Set
to `"application/json"` if a legacy frontend cannot yet parse
`application/problem+json`. Set to `None` to leave DRF's negotiated
content type untouched.

### `INCLUDE_INSTANCE`

- **Type:** `bool`
- **Default:** `True`

When `True`, the `instance` member is set to the request's path
(`request.path`), per RFC 9457 section 3.1.4.

### `INCLUDE_CORRELATION_ID`

- **Type:** `bool`
- **Default:** `True`

When `True`, a `correlation_id` extension member is included, sourced
from [`CorrelationIdMiddleware`](api-reference.md#correlationidmiddleware).

### `INCLUDE_REQUEST_ID`

- **Type:** `bool`
- **Default:** `True`

When `True`, a `request_id` extension member is included.

### `INCLUDE_TRACE_ID`

- **Type:** `bool`
- **Default:** `True`

When `True`, a `trace_id` extension member is included whenever a W3C
`traceparent` header was present on the request.

### `INCLUDE_TIMESTAMP`

- **Type:** `bool`
- **Default:** `True`

When `True`, a `timestamp` extension member (ISO 8601, UTC) is included.

### `EXPAND_VALIDATION_ERRORS`

- **Type:** `bool`
- **Default:** `True`

When `True`, validation errors are expanded into an `errors` extension
array of `{"pointer", "detail", "code"}` objects, one per invalid field
(including nested serializers). When `False`, validation errors are
treated like any other `APIException` (a single flattened `detail`
string, no `errors` array).

### `SERVER_ERROR_DETAIL`

- **Type:** `str`
- **Default:** `"A server error occurred. Please try again later."`

The `detail` message used for uncaught, non-`APIException` exceptions
(500s). Never make this leak exception internals in production.

### `CATCH_ALL_EXCEPTIONS`

- **Type:** `bool`
- **Default:** `True`

When `True`, unhandled exceptions that are not `APIException` subclasses
(e.g. a raw `ValueError` bubbling out of a view) are converted into a 500
Problem Details response. When `False`, such exceptions are left for
Django's own `DEBUG`-aware error handling (the handler returns `None`,
matching DRF's own `exception_handler` contract).

### `STANDARDIZED_ERRORS_COMPAT`

- **Type:** `bool`
- **Default:** `False`

When `True`, adds a `standardized_errors` extension member matching
`drf-standardized-errors`' response shape, for projects migrating from
that package. See [FAQ](faq.md#migrating-from-drf-standardized-errors).
