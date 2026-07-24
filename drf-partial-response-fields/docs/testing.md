# Testing

## Running the package's own test suite

```bash
git clone https://github.com/mahmoudgshaker/drf-partial-response-fields.git
cd drf-partial-response-fields
pip install -e ".[dev]"
pytest
```

Run the full compatibility matrix across every supported Python/Django
combination:

```bash
tox
```

Run with coverage:

```bash
pytest --cov --cov-report=term-missing
```

Run only the benchmarks:

```bash
pytest --benchmark-only
```

## Testing views with `PartialResponseMixin`

### Via the DRF test client (recommended)

```python
from rest_framework.test import APIClient
import pytest


@pytest.mark.django_db
def test_fields_param_narrows_response(article):
    client = APIClient()
    response = client.get("/articles/?fields=title,author(name)")
    assert response.status_code == 200
    assert set(response.data["results"][0]) == {"id", "title", "author"}
```

### Constructing a view instance directly

Useful for unit-testing `get_queryset()` / `get_serializer_context()`
without a full URL dispatch:

```python
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory


def test_get_queryset_is_optimized(api_rf: APIRequestFactory):
    view = ArticleViewSet()
    view.request = Request(api_rf.get("/articles/?fields=title,author(name)"))
    view.format_kwarg = None
    view.kwargs = {}
    qs = view.get_queryset()
    assert "author" in qs.query.select_related
```

Note the request must be wrapped in `rest_framework.request.Request` — a
raw `APIRequestFactory` request has no `.query_params`, which
`parse_request_fields()` depends on.

## Testing serializers directly

```python
from drf_partial_response_fields.constants import CONTEXT_KEY
from drf_partial_response_fields.parser import parse_fields


def test_nested_selection(article):
    tree = parse_fields("title,author(name)")
    serializer = ArticleSerializer(article, context={CONTEXT_KEY: tree})
    assert set(serializer.data["author"]) == {"id", "name"}
```

## Asserting query counts

Use `django_assert_num_queries` (from `pytest-django`) or
`django.test.utils.CaptureQueriesContext` directly:

```python
def test_no_n_plus_one(django_assert_num_queries, many_articles):
    tree = parse_fields("title,author(name)")
    qs = optimize_queryset(Article.objects.all(), ArticleSerializer, tree)
    serializer = ArticleSerializer(qs, many=True, context={CONTEXT_KEY: tree})
    with django_assert_num_queries(1):
        _ = serializer.data
```

## Testing custom `SerializerMethodField` optimizer hints

Assert on the built queryset directly rather than counting queries, so the
test documents *why* a particular join exists:

```python
def test_editor_note_hint_adds_select_related():
    tree = parse_fields("editor_note")
    qs = optimize_queryset(Article.objects.all(), ArticleSerializer, tree)
    assert qs.query.select_related == {"author": {"profile": {}}}
```

## Property-based testing the parser

If you build tooling on top of `parse_fields()` (a custom UI query builder,
for example), consider a `hypothesis` strategy generating valid field
expressions to fuzz your integration, following the pattern in
`tests/test_parser.py::TestPropertyBased`.

## Testing with a real Redis / external services

This package has no external service dependencies (no Redis, no cache
backend) — every test in its own suite runs against SQLite in memory with
`--no-migrations`. If your project layers caching on top of this package's
output, test that separately from field-selection behavior.
