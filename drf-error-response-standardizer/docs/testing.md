# Testing

## Running this package's own test suite

```bash
pip install -e ".[test]"
pytest
```

With coverage:

```bash
pytest --cov --cov-report=term-missing
```

Across the full Python/Django support matrix via [tox](https://tox.wiki):

```bash
tox
```

## Testing views that use this package

Assert on `code`, not on `title`/`detail` wording (see
[Common Patterns](common-patterns.md#testing-that-a-view-returns-the-right-problem-type)):

```python
import pytest


@pytest.mark.django_db
def test_missing_title_returns_validation_error(api_client):
    response = api_client.post("/articles/", {"body": "..."}, format="json")

    assert response.status_code == 400
    assert response.data["code"] == "validation_error"
    pointers = {e["pointer"] for e in response.data["errors"]}
    assert "title" in pointers
```

## Testing a custom exception mapping in isolation

Build a throwaway `ProblemRegistry` rather than mutating
`default_registry`, so tests cannot leak state into each other:

```python
from drf_error_response_standardizer.codes import ErrorType
from drf_error_response_standardizer.handler import problem_details_exception_handler
from drf_error_response_standardizer.registry import ProblemRegistry


def test_out_of_stock_mapping(api_rf):
    registry = ProblemRegistry()
    registry.register(
        OutOfStockError,
        ErrorType(code="out_of_stock", title="Item Out of Stock", slug="out-of-stock", status=409),
    )

    response = problem_details_exception_handler(
        OutOfStockError(), {"request": api_rf.get("/")}, registry=registry
    )

    assert response is not None
    assert response.data["code"] == "out_of_stock"
```

If you *do* need to register against `default_registry` directly (e.g.
testing your project's `AppConfig.ready()` wiring), always clean up in a
`finally` block or a fixture teardown:

```python
import pytest
from drf_error_response_standardizer.registry import default_registry, register


@pytest.fixture
def registered_out_of_stock():
    register(OutOfStockError, out_of_stock_error_type)
    yield
    default_registry.unregister(OutOfStockError)
```

## `override_settings` works out of the box

Every `ERROR_RESPONSE_STANDARDIZER` setting is cache-invalidated on
Django's `setting_changed` signal, so `@override_settings` (or the
context-manager form) works exactly as expected in tests without any
extra setup:

```python
from django.test import override_settings


def test_catch_all_disabled():
    with override_settings(ERROR_RESPONSE_STANDARDIZER={"CATCH_ALL_EXCEPTIONS": False}):
        ...
```

## Fixtures used by this package's own suite

`tests/conftest.py` provides `api_rf` (an `APIRequestFactory`) and
`api_client` (an `APIClient`) fixtures used throughout
`tests/test_handler.py` and `tests/test_integration.py` - copy this
pattern into your own project's `conftest.py` if you do not already have
equivalents.
