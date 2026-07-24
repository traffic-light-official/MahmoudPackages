# Common Patterns

## Generating the error catalog in CI

Fail a build if a new problem type is introduced without documenting it:

```yaml
# .github/workflows/ci.yml
- name: Check error catalog is up to date
  run: |
    python manage.py generate_error_catalog --format=markdown --output=docs/errors.md
    git diff --exit-code docs/errors.md
```

## Per-app problem type modules

For a project with many domain exceptions, keep the registrations next
to the exceptions they describe rather than in one large file:

```python
# billing/exceptions.py
from drf_error_response_standardizer.codes import ErrorType
from drf_error_response_standardizer.registry import register


class PaymentDeclinedError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


register(
    PaymentDeclinedError,
    ErrorType(code="payment_declined", title="Payment Declined", slug="payment-declined", status=402),
)
```

Import each app's `exceptions` module from its `AppConfig.ready()` so
registration happens exactly once, at startup, regardless of import
order.

## Scoping a registry per API version

If different API versions must return different problem types for the
same exception, do not mutate `default_registry` - build a
`ProblemRegistry` per version and bind it with `functools.partial`:

```python
from functools import partial

from drf_error_response_standardizer.handler import problem_details_exception_handler
from drf_error_response_standardizer.registry import ProblemRegistry

v2_registry = ProblemRegistry()
# ... v2_registry.register(...) for v2-specific mappings ...

v2_exception_handler = partial(problem_details_exception_handler, registry=v2_registry)
```

Then point a versioned `REST_FRAMEWORK` override, or a specific
`ViewSet.get_exception_handler()` override, at `v2_exception_handler`.

## Testing that a view returns the right problem type

```python
def test_out_of_stock_returns_409(api_client, product):
    product.stock = 0
    product.save()

    response = api_client.post(f"/orders/", {"product_id": product.id}, format="json")

    assert response.status_code == 409
    assert response.data["code"] == "out_of_stock"
```

Because `ProblemDetail.to_dict()` always includes `code`, tests should
assert on `code`, never on `title` or `detail` text - those are meant to
change (wording fixes, localization) without being a breaking API
change. See [Testing](testing.md).

## Frontend error handling

A typical frontend integration branches on `code`, falls back to
`detail` for display, and surfaces `errors` next to the relevant form
fields:

```javascript
async function submitArticle(payload) {
  const response = await fetch("/api/articles/", {
    method: "POST",
    body: JSON.stringify(payload),
    headers: { "Content-Type": "application/json" },
  });
  if (!response.ok) {
    const problem = await response.json();
    if (problem.errors) {
      for (const { pointer, detail } of problem.errors) {
        setFieldError(pointer.replace(/\//g, "."), detail);
      }
    } else {
      showToast(problem.detail);
    }
    return;
  }
  return response.json();
}
```
