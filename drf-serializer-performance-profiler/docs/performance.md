# Performance

## Zero overhead when both settings are off

`ProfileSerializerMixin.to_representation()`'s very first line checks
`ENABLED`/`LOG_SLOW_FIELDS`; with both `False` (the default), it
delegates straight to `super().to_representation()` - no timing, no
query counting, no dict allocation beyond what the real serializer
already does. This package is safe to leave mixed into every serializer
in a codebase permanently, since the disabled path costs exactly one
settings lookup pair per `to_representation()` call (not per field).

## The instrumentation cost when it's on

Each field's measurement costs one `time.perf_counter()` pair and one
`ExitStack`/`execute_wrapper()` setup/teardown per field, plus one
small dataclass allocation the first time that field name is seen. For
a serializer with a handful of fields, this is a small, fixed overhead
per row - noticeable if profiling a very high-throughput endpoint
continuously, which is exactly why `ENABLED` defaults to `False` and is
meant for targeted debugging, not always-on production traffic (use
`LOG_SLOW_FIELDS` for that instead - see below).

## `LOG_SLOW_FIELDS` is meant to be safe for continuous production use

Unlike the header mechanism (meant for one investigation at a time),
`LOG_SLOW_FIELDS` is designed to be left on indefinitely: the
per-field overhead is the same either way, but there's no response
mutation, no `RESTRICT_TO_STAFF` check per request, and no header
string formatting on the hot path - only a conditional log call for
fields that actually exceed the threshold. Most requests, where every
field is fast, pay only the underlying `measure()` cost with no log
call at all.

## `connection.execute_wrapper()` has no query-count limit or sampling

Every single query is counted, exactly - there's no sampling or
approximation, unlike some APM tools that sample a percentage of
requests. This makes the numbers exact for debugging a specific
request, but means the cost scales with the actual number of queries a
field triggers - a field issuing thousands of queries per row (a
severe N+1) makes the *instrumentation* itself proportionally more
expensive too, not just the underlying queries. In practice this is
rarely the bottleneck, since the queries themselves already dominate.

## Recommended: profile against production-representative data volumes

A field's query count is often proportional to something in your data
(number of comments, number of tags) - profiling against a mostly-empty
development database can understate a field's real-world cost. Seed
representative row counts (see `examples/blog/example.py`'s pattern)
before trusting a profile's numbers as representative of production
behavior.

## Aggregated numbers hide per-row variance

`FieldProfile.total_time_ms`/`.query_count` are sums across every row -
`average_time_ms` divides by `call_count` for a per-row average, but
neither number tells you whether one unusually slow/expensive row is
skewing the total. If you suspect a single outlier row rather than a
uniformly slow field, profile a single instance directly
(`ArticleSerializer(single_article).data`) instead of a list.
