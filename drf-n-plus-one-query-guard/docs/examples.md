# Examples

A complete, runnable example - no separate Django project needed - lives
in [`examples/blog/`](https://github.com/MahmoudGShake/MahmoudPackages/tree/master/drf-n-plus-one-query-guard/examples/blog):
an `Author`/`Article` model pair (`models.py`) and a script
(`example.py`) that configures Django inline, creates five articles
each with their own author, then demonstrates the exact
catch-then-fix cycle this package exists for.

## Running it

```bash
python -m examples.blog.example
```

```
Creating test database for alias 'default'...
Unoptimized: expect an AssertionError...
  Article 0 by Author 0
  Article 1 by Author 1
  Article 2 by Author 2
  Article 3 by Author 3
  Article 4 by Author 4
Caught: Suspected N+1 queries detected:
  5x 'SELECT "blog_author"."id", "blog_author"."name" FROM "blog_author" WHERE "blog_author"."id" = %s LIMIT 21' (first at example.py:45)

Optimized with select_related('author'): expect no error...
  Article 0 by Author 0
  Article 1 by Author 1
  Article 2 by Author 2
  Article 3 by Author 3
  Article 4 by Author 4
No N+1 detected.
Destroying test database for alias 'default'...
```

Note the message names the *exact* repeated fingerprint (the
`blog_author` lookup by primary key), the count (`5x`, matching the
five articles), and the call site (`example.py:45`, the
`article.author.name` access inside the loop) - not just "6 queries
were executed instead of 2."

## The code

```python
# examples/blog/models.py
from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=200)


class Article(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
```

```python
# examples/blog/example.py (abbreviated)
from drf_n_plus_one_query_guard import assert_no_n_plus_one

try:
    with assert_no_n_plus_one():
        for article in Article.objects.all():
            print(f"  {article.title} by {article.author.name}")
except AssertionError as exc:
    print(f"Caught: {exc}")

# fixed:
with assert_no_n_plus_one():
    for article in Article.objects.select_related("author").all():
        print(f"  {article.title} by {article.author.name}")
```

## In a real DRF project instead

The same pattern, against a real endpoint via `APIClient` rather than a
raw queryset loop:

```python
from drf_n_plus_one_query_guard import assert_no_n_plus_one


def test_article_list_has_no_n_plus_one(api_client):
    with assert_no_n_plus_one():
        api_client.get("/articles/")
```

See [Getting Started](getting-started.md) for the corresponding
`ArticleViewSet`/serializer shape that triggers (and the
`select_related` fix that resolves) this exact failure.
