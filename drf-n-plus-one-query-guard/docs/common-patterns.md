# Common Patterns

## Ignoring a specific known-acceptable query

Some repeated queries are genuinely fine (a small, fixed-size lookup
loop, or a pattern you've deliberately decided not to optimize yet).
Rather than raising `THRESHOLD` project-wide - which hides *every*
N+1 up to that count, not just the one you reviewed - allowlist the
specific query:

```python
N_PLUS_ONE_GUARD = {
    "IGNORE_PATTERNS": [r"myapp_taggeditem"],
}
```

Or, scoped to a single test rather than the whole project:

```python
def test_article_list(api_client):
    with assert_no_n_plus_one(ignore_patterns=["myapp_taggeditem"]):
        api_client.get("/articles/")
```

## Gating CI on N+1s without touching production behavior

Set `MODE = "raise"` only for the test settings module, never the
production one:

```python
# myproject/settings/test.py
from .base import *  # noqa: F401,F403

N_PLUS_ONE_GUARD = {"MODE": "raise"}
```

Combined with `NPlusOneGuardMiddleware`, every test hitting any view
through the Django test client now fails loudly on a new N+1, without
writing `assert_no_n_plus_one()` into every single test - useful as a
blanket safety net, with `assert_no_n_plus_one()` reserved for the
specific endpoints you want a self-documenting, explicit assertion for.

## Testing a nested/related endpoint

The same pattern catches N+1s introduced by nested serialization, not
just a flat list:

```python
def test_article_detail_includes_comments_without_n_plus_one(api_client, article):
    with assert_no_n_plus_one():
        api_client.get(f"/articles/{article.id}/")
```

If `ArticleSerializer` nests a `CommentSerializer(many=True)` and the
view's queryset doesn't `prefetch_related("comments")`, this fails with
the comments table's fingerprint - exactly the same as the
`select_related` case, just for a reverse FK/M2M instead of a forward
FK.

## Checking a whole test suite at once, not endpoint-by-endpoint

For an existing project without per-endpoint `assert_no_n_plus_one()`
coverage yet, enable `NPlusOneGuardMiddleware` with `MODE = "warn"`
against your CI's real test suite run and grep the log output for
`"Suspected N+1"` - this surfaces every N+1 across every existing test
without writing new assertions, as a starting inventory to work through.

## Distinguishing "acceptable N+1" from "forgot to optimize"

A repeated query at a *low*, fixed count is a different signal than one
whose count scales with request size (e.g. 25 repeats because the page
size is 25) - the latter is the pattern actually worth fixing. Use the
`QueryTracker`/`NPlusOneGuard` lower-level API directly (see
[Advanced Usage](advanced-usage.md#using-nplusoneguard-directly-for-custom-dispatch))
if you need to inspect `violation.count` against your fixture size
rather than just failing on any repeat at all. In practice, prefer
`ignore_patterns` (see above) for a query you've deliberately reviewed
and accepted - it documents the decision at the specific query, rather
than in ad hoc assertion logic scattered across tests.
