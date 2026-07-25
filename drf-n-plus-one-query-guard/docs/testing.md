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

## The core assertion

```python
from drf_n_plus_one_query_guard import assert_no_n_plus_one


def test_article_list_has_no_n_plus_one(api_client):
    with assert_no_n_plus_one():
        api_client.get("/articles/")
```

## Asserting a specific violation count when you expect exactly one

Useful when tightening an existing test suite incrementally - assert
the *current* known state, then fix and drop the assertion:

```python
from drf_n_plus_one_query_guard.tracker import QueryTracker


def test_current_n_plus_one_is_exactly_one_violation(api_client):
    with QueryTracker() as tracker:
        api_client.get("/articles/")

    violations = tracker.violations(threshold=2)
    assert len(violations) == 1
    assert violations[0].count == 25  # matches this test's known page size
```

## Testing with a custom threshold

```python
def test_a_small_fixed_repeat_is_tolerated(api_client):
    with assert_no_n_plus_one(threshold=3):
        api_client.get("/articles/")  # tolerates up to 2 repeats
```

## Testing the middleware directly, without a full request

```python
from django.test import RequestFactory, override_settings

from drf_n_plus_one_query_guard.middleware import NPlusOneGuardMiddleware


def test_middleware_adds_header_on_violation(article_factory):
    article_factory.create_batch(5)  # each with a distinct author
    middleware = NPlusOneGuardMiddleware(my_n_plus_one_view)
    request = RequestFactory().get("/articles/")

    with override_settings(DEBUG=True, N_PLUS_ONE_GUARD={"MODE": "report"}):
        response = middleware(request)

    assert "X-N-Plus-One-Warnings" in response
```

## Testing that a real exception isn't masked

Both `assert_no_n_plus_one()` and `NPlusOneGuard` let a genuine
exception from the guarded code propagate untouched, even if a
violation was also found - verify this holds for your own wrapping
code, if you write any:

```python
import pytest


def test_a_real_failure_still_propagates(api_client):
    with pytest.raises(SomeOtherError):
        with assert_no_n_plus_one():
            call_the_thing_that_both_has_an_n_plus_one_and_raises()
```

## Fixtures used by this package's own suite

`tests/conftest.py` provides `api_client`, `make_author`, `make_article`,
and `several_articles` (five articles, each with its own author - the
classic N+1 shape) fixtures, against a real `tests/test_app` with
`Author`/`Article` models and both an unoptimized `ArticleViewSet` and
an optimized `OptimizedArticleViewSet` - reuse this shape in your own
project's `conftest.py` rather than re-deriving fixtures from scratch.
