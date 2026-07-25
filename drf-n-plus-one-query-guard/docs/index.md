# drf-n-plus-one-query-guard

Detect N+1 query patterns in Django REST Framework views - in tests, in
development, and (opt-in) in production - by fingerprinting repeated
SQL shapes, not just counting total queries.

```python
from drf_n_plus_one_query_guard import assert_no_n_plus_one


def test_article_list_has_no_n_plus_one(api_client):
    with assert_no_n_plus_one():
        api_client.get("/articles/")
```

## Why this exists

A plain "assert query count <= N" test breaks every time you add an
unrelated, legitimate query, and tells you nothing about *which* query
is the problem when it fails. This package fingerprints each executed
query's normalized SQL shape and flags a shape that repeats at least
`THRESHOLD` times within one guarded scope - which is exactly what an
N+1 looks like (one query per row of an un-prefetched loop) - along
with the first application code location that triggered it.

## Where to go next

- New to the package? Start with [Getting Started](getting-started.md).
- Writing a test right now? Jump straight to
  [`assert_no_n_plus_one()`](api-reference.md#assert_no_n_plus_one).
- Want to guard every request during development? See
  [Advanced Usage](advanced-usage.md#middleware).
- Want to know exactly how detection works? Read [Architecture](architecture.md).
- Something not behaving as expected? Check [Troubleshooting](troubleshooting.md)
  and the [FAQ](faq.md).

## At a glance

| Task | Where |
| --- | --- |
| Assert no N+1 in a test | [`assert_no_n_plus_one()`](api-reference.md#assert_no_n_plus_one) |
| Guard every request in dev/staging | [`NPlusOneGuardMiddleware`](api-reference.md#nplusoneguardmiddleware) |
| Guard one view/action | [`guard_view()`](api-reference.md#guard_view) |
| Low-level query capture | [`QueryTracker`](api-reference.md#querytracker) |
| Configure threshold/mode/ignore list | [Settings](settings.md) |
