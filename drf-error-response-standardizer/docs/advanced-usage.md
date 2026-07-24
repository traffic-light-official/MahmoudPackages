# Advanced Usage

## Custom exception mapping

Two ways to map a raised exception onto a problem response, in
increasing order of control.

### 1. A fixed `ErrorType`

Best when the title/status/code never depend on the exception instance:

```python
from drf_error_response_standardizer.codes import ErrorType
from drf_error_response_standardizer.registry import register

register(
    OutOfStockError,
    ErrorType(code="out_of_stock", title="Item Out of Stock", slug="out-of-stock", status=409),
)
```

Registration is by class and honors subclassing: registering a base
class also covers subclasses that have no more specific registration of
their own, and a more specific registration always wins.

### 2. A custom builder

Best when the `detail` or an extension member must be derived from the
exception instance:

```python
from drf_error_response_standardizer.problem import ProblemDetail
from drf_error_response_standardizer.registry import register_builder


def build_out_of_stock_problem(exc: OutOfStockError) -> ProblemDetail:
    return ProblemDetail(
        status=409,
        title="Item Out of Stock",
        code="out_of_stock",
        detail=f"{exc.product.name} is out of stock.",
        extensions={"product_id": exc.product.id, "restock_eta": exc.restock_eta.isoformat()},
    )


register_builder(OutOfStockError, build_out_of_stock_problem)
```

### 3. `ProblemAPIException`

Best when you control the raise site and want full control without
touching the registry at all - see [`ConflictError`](api-reference.md#conflicterror)
and [`UnprocessableEntityError`](api-reference.md#unprocessableentityerror)
for ready-made examples, or subclass
[`ProblemAPIException`](api-reference.md#problemapiexception) directly.

## Generating the error catalog

```python
from drf_error_response_standardizer.catalog import build_catalog, render_markdown

catalog = build_catalog()  # every ErrorType registered anywhere
print(render_markdown(catalog))
```

Or from the command line:

```bash
python manage.py generate_error_catalog --format=markdown --output=docs/errors.md
```

Wire this into CI to fail the build if the catalog changed without a
matching documentation update - see
[Common Patterns](common-patterns.md#generating-the-error-catalog-in-ci).

## OpenAPI integration

```python
SPECTACULAR_SETTINGS = {
    "POSTPROCESSING_HOOKS": [
        "drf_error_response_standardizer.openapi.problem_details_postprocessing_hook",
    ],
}
```

This registers a `ProblemDetail` component schema and, for every
operation, a default `application/problem+json` response for any
undocumented status code in `{400, 401, 403, 404, 405, 406, 409, 415,
422, 429, 500}` (only codes not already declared via
`@extend_schema(responses=...)` are touched). To restrict the codes to
only what your project's registry can actually produce:

```python
from drf_error_response_standardizer.openapi import registered_status_codes

print(registered_status_codes())  # e.g. [400, 401, 403, 404, 405, 406, 415, 429]
```

## Localization

```python
from django.utils.translation import gettext_lazy as _
from drf_error_response_standardizer.codes import ErrorType
from drf_error_response_standardizer.registry import register

register(
    OutOfStockError,
    ErrorType(code="out_of_stock", title=str(_("Item Out of Stock")), slug="out-of-stock", status=409),
)
```

`problem_details_exception_handler` wraps problem construction in
`activate_for_request(request)`, which activates the language resolved
from the request's `Accept-Language` header (via Django's standard
`get_language_from_request`) for the duration of the call - so any
string passed through `translate()` (used internally for built-in titles
and messages) comes back in the client's preferred language, even on
projects that do not install Django's `LocaleMiddleware`. Provide
translations for your own strings the same way you would for any other
Django project: a `.po` file per locale, compiled with
`django-admin compilemessages`.

## Correlation IDs across services

`CorrelationIdMiddleware` preserves an incoming `X-Correlation-ID`
header rather than always generating a new one, so a value set by an
upstream gateway or a calling service propagates through your entire
call graph:

```python
import httpx
from drf_error_response_standardizer.middleware import get_correlation_id


def call_downstream_service(request):
    headers = {"X-Correlation-ID": get_correlation_id(request) or ""}
    return httpx.get("https://downstream.example.com/api/", headers=headers)
```

## `drf-standardized-errors` migration

See [FAQ](faq.md#migrating-from-drf-standardized-errors).
