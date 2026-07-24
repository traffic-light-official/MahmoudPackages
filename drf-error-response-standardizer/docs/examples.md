# Examples

A runnable example project lives in [`examples/blog/`](https://github.com/MahmoudGShake/MahmoudPackages/tree/master/drf-error-response-standardizer/examples/blog)
in the repository: models, serializers, a `ViewSet`, and settings wiring
everything together.

## Validation error (single field)

```http
POST /articles/
Content-Type: application/json

{"body": "Missing a title."}
```

```json
{
  "type": "about:blank",
  "title": "Validation Error",
  "status": 400,
  "detail": "One or more fields failed validation.",
  "instance": "/articles/",
  "code": "validation_error",
  "errors": [{ "pointer": "title", "detail": "This field is required.", "code": "required" }]
}
```

## Validation error (nested serializer)

```http
POST /articles/
Content-Type: application/json

{"title": "Hi", "body": "...", "author": {"name": "Ada", "email": "not-an-email"}}
```

```json
{
  "type": "about:blank",
  "title": "Validation Error",
  "status": 400,
  "detail": "One or more fields failed validation.",
  "instance": "/articles/",
  "code": "validation_error",
  "errors": [
    { "pointer": "author/email", "detail": "Enter a valid email address.", "code": "invalid" }
  ]
}
```

## Not found

```http
GET /articles/999/
```

```json
{
  "type": "about:blank",
  "title": "Resource Not Found",
  "status": 404,
  "detail": "Not found.",
  "instance": "/articles/999/",
  "code": "not_found"
}
```

## Not authenticated

```http
GET /admin-only/
```

```json
{
  "type": "about:blank",
  "title": "Authentication Required",
  "status": 401,
  "detail": "Authentication credentials were not provided.",
  "instance": "/admin-only/",
  "code": "not_authenticated"
}
```

Response headers also include `WWW-Authenticate`, exactly as DRF's own
default handler would set it.

## Throttled

```http
GET /rate-limited/
```

```json
{
  "type": "about:blank",
  "title": "Request Throttled",
  "status": 429,
  "detail": "Request was throttled. Expected available in 34 seconds.",
  "instance": "/rate-limited/",
  "code": "throttled"
}
```

Response headers include `Retry-After: 34`.

## Custom domain exception

```python
from drf_error_response_standardizer.exceptions import ConflictError

raise ConflictError("Order has already shipped.", extensions={"order_id": 42})
```

```json
{
  "type": "about:blank",
  "title": "Conflict",
  "status": 409,
  "detail": "Order has already shipped.",
  "instance": "/orders/42/",
  "code": "conflict",
  "order_id": 42
}
```

## Uncaught exception (500)

```json
{
  "type": "about:blank",
  "title": "Internal Server Error",
  "status": 500,
  "detail": "A server error occurred. Please try again later.",
  "instance": "/articles/",
  "code": "server_error"
}
```

Note the original exception message is never leaked to the client - see
[Security](security.md).
