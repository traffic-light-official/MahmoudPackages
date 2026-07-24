# drf-error-response-standardizer

[RFC 9457 Problem Details](https://www.rfc-editor.org/rfc/rfc9457.html) for
Django REST Framework: one consistent, machine-readable JSON shape for
every error response your API returns, whether it comes from DRF itself
(validation, permissions, throttling), Django (`Http404`,
`PermissionDenied`), your own domain code, or an uncaught bug.

```json
{
  "type": "https://api.example.com/problems/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "One or more fields failed validation.",
  "instance": "/api/articles/",
  "code": "validation_error",
  "errors": [
    { "pointer": "title", "detail": "This field is required.", "code": "required" }
  ]
}
```

## Why this exists

DRF's default exception handler produces three different response shapes
depending on what went wrong, offers clients nothing but English prose to
branch on, and returns nothing at all for uncaught exceptions. As an API
grows past a handful of endpoints, that inconsistency becomes a real
integration cost for every client. `drf-error-response-standardizer`
replaces the handler with a single RFC-compliant shape and the supporting
machinery to keep it consistent:

1. **Standardization** — every error, from every source, comes back as
   the same `type`/`title`/`status`/`detail`/`instance` shape.
2. **Machine-readability** — a stable `code` and, for validation errors, a
   flat `errors` array with JSON-Pointer-style paths, so clients never
   parse English text to decide what to do.
3. **Traceability** — correlation IDs, request IDs, and W3C trace IDs are
   attached automatically, on both success and error responses.

See [Architecture](architecture.md) for how the pieces fit together.

## Where to go next

- New to the package? Start with [Getting Started](getting-started.md).
- Wiring it into an existing project? See [Installation](installation.md)
  and [Configuration](configuration.md).
- Want the full picture of how it works? Read [Architecture](architecture.md).
- Looking for a specific class or setting? Jump to
  [API Reference](api-reference.md) or [Settings](settings.md).
- Something not behaving as expected? Check [Troubleshooting](troubleshooting.md)
  and the [FAQ](faq.md).

## At a glance

| Task | Where |
| --- | --- |
| Install the exception handler | [`problem_details_exception_handler`](api-reference.md#problem_details_exception_handler) |
| Propagate correlation/request/trace IDs | [`CorrelationIdMiddleware`](api-reference.md#correlationidmiddleware) |
| Raise a custom problem from view code | [`ProblemAPIException`](api-reference.md#problemapiexception) |
| Map an existing exception class | [`register`](api-reference.md#register) |
| Generate an error catalog | [`generate_error_catalog`](common-patterns.md#generating-the-error-catalog-in-ci) |
| Document errors in OpenAPI | [`problem_details_postprocessing_hook`](api-reference.md#problem_details_postprocessing_hook) |
| Change response shape/behavior | [Settings](settings.md) |
