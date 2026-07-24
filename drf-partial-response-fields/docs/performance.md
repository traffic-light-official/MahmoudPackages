# Performance

## Measured query-count reduction

`tests/test_benchmarks.py::TestQueryCountBenchmark` asserts this exactly,
so it's enforced by CI rather than just claimed here: serializing **50**
articles (each with an author and a tag) via
`ArticleSerializer(qs, many=True)` with `?fields=title,author(name),tags(label)`
takes exactly **2** queries total — 1 for the articles (with `author`
joined via `select_related`) and 1 batched `prefetch_related` for `tags` —
regardless of whether there are 5 articles or 5,000. Without
`optimize_queryset()`, naively accessing `article.author.name` for each of
50 articles takes 50+ queries (one per article) — see
`TestQueryCountReduction::test_unoptimized_baseline_triggers_n_plus_one` in
`tests/test_optimizer.py`.

`TestQueryCountReduction::test_narrow_selection_uses_fewer_queries_than_full_selection`
further asserts that a narrower `fields=title` request issues *fewer*
queries than the full default representation of the same object graph —
proving that requesting less genuinely costs less, not just that the
worst case is bounded.

## Why this matters more than payload size

Removing unrequested keys from a JSON response saves bytes on the wire.
Removing the *joins and prefetches* those keys would have required saves
database round-trips and connection-pool pressure — typically the larger
cost by an order of magnitude for anything beyond a trivial payload. This
package treats the two as equally important; most sparse-fieldset
libraries only do the first.

## Micro-benchmarks

`tests/test_benchmarks.py` also includes `pytest-benchmark` timings for the
parser and the optimizer's queryset-construction overhead (no database
access — pure Python object walking):

```bash
pytest --benchmark-only
```

On typical hardware, parsing a moderately complex expression
(`id,title,author(name,email,profile(display_name)),tags(label),comments(author_name,text)`)
takes well under 100 microseconds, and `optimize_queryset()`'s own
bookkeeping (excluding the actual database round-trip) is in the same
range. Both are negligible next to a single database round-trip (typically
0.5–5ms even on a fast local connection), so the optimizer pays for itself
after preventing a single avoided query.

## What the optimizer does and does not do

| Optimization | Applied when |
| --- | --- |
| `select_related` | Forward FK/O2O or reverse O2O exposed as a nested serializer, or any relation field that isn't DRF's own pk-only optimized (e.g. `SlugRelatedField`) |
| `prefetch_related` (plain) | M2M or reverse FK exposed as anything other than a nested serializer or pk-only `PrimaryKeyRelatedField(many=True)` |
| `prefetch_related` (nested `Prefetch`, recursively optimized) | M2M or reverse FK exposed as a nested serializer — the nested queryset is itself passed back through `optimize_queryset()` |
| `prefetch_related` (restricted to `.only("pk", ...)`) | M2M or reverse FK exposed as `PrimaryKeyRelatedField(many=True)` |
| `only()` | Any plain concrete model column, and any queryset annotation matching a requested field name |
| Nothing (left alone) | `@property`, unmapped computed attributes, `GenericForeignKey`, DRF's own pk-only-optimized single relations (no join needed) |

See [Architecture](architecture.md#the-query-optimizers-decision-tree) for
the full decision tree and [Troubleshooting](troubleshooting.md) for what
"left alone" means in practice.

## Benchmarking your own views

```python
from django.test.utils import CaptureQueriesContext
from django.db import connection

with CaptureQueriesContext(connection) as ctx:
    response = client.get("/articles/?fields=title,author(name)")

print(len(ctx.captured_queries))
for query in ctx.captured_queries:
    print(query["sql"])
```

Run this once with a narrow `fields=` selection and once with none (full
representation) to see the difference directly against your own models
and data volume — the reduction scales with how relationally "wide" your
default representation is and how narrow the client's request is.
