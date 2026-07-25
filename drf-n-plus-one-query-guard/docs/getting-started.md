# Getting Started

## Install

```bash
pip install drf-n-plus-one-query-guard
```

```python
# settings.py
INSTALLED_APPS = [
    ...,
    "drf_n_plus_one_query_guard",
]
```

## Write a test that would have caught the bug

```python
from drf_n_plus_one_query_guard import assert_no_n_plus_one


def test_article_list_has_no_n_plus_one(api_client):
    with assert_no_n_plus_one():
        api_client.get("/articles/")
```

If `ArticleViewSet`'s queryset doesn't call `select_related("author")`
(or `prefetch_related`, for a many-to-many/reverse FK), and the
serializer accesses `article.author` per row, this fails with:

```
AssertionError: Suspected N+1 queries detected:
  5x 'SELECT ... FROM myapp_author WHERE id = %s' (first at serializers.py:12)
```

Fix it the normal way:

```python
class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.select_related("author").all()
```

Re-run the test - it passes, because the same query fingerprint no
longer repeats.

## Guard every request during development

```python
# settings.py
MIDDLEWARE = [
    ...,
    "drf_n_plus_one_query_guard.middleware.NPlusOneGuardMiddleware",
]
```

With `settings.DEBUG = True`, any request with a suspected N+1 gets an
`X-N-Plus-One-Warnings` response header - visible in your browser's dev
tools or `curl -i` without failing the request. See
[Advanced Usage](advanced-usage.md#middleware) for `raise` mode, which
does fail the request (development/CI/staging only - never production,
see [Security](security.md)).

## Guard one specific view

```python
from drf_n_plus_one_query_guard import guard_view


class ArticleViewSet(viewsets.ModelViewSet):
    @guard_view(mode="raise")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
```

## What counts as "the same query"

Two executions of an ORM-generated query with the same *shape* but
different parameter values (e.g. a different `author_id` per loop
iteration) are already parameterized identically by Django's ORM before
reaching the database - `SELECT ... WHERE author_id = %s` regardless of
which id - so no literal-stripping is needed to recognize them as the
same fingerprint. See [Architecture](architecture.md) for the full
detection algorithm.
