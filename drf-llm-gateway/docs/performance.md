# Performance

## Where the cost actually is

Schema generation (`serializer_to_json_schema`) is pure Python object
introspection — instantiate a serializer, walk `instance.fields`, map
each field's type. There is no database I/O in this path at all. The
measurable cost in any real deployment is the *dispatch* — `execute_tool`
constructs and processes a real DRF request, so its cost is the same as
any other API call through that viewset: authentication, permission
checks, serializer validation, and the underlying database queries your
view performs.

## Schema generation is cheap and safe to call often

Because schemas aren't cached or frozen (see
[Architecture](architecture.md#why-schemas-arent-frozen-at-registration-time)),
`to_openai_tools()` / `to_mcp_tools()` re-walk every registered
serializer's fields on every call. For a typical project with dozens of
tools and single-digit-count fields per serializer, this is sub-millisecond
work — safe to call per-request if your agent framework wants fresh
schemas every time, though most integrations should cache the exported
list and only regenerate when `schema_hash` changes (see
[Advanced Usage](advanced-usage.md#schema-versioning-in-practice)).

## `MAX_SCHEMA_DEPTH` and `MAX_ENUM_VALUES` bound worst case

A pathological serializer graph (deeply nested serializers, or a
`ChoiceField` with thousands of options) is the only way schema generation
could become expensive or produce an unusably large schema. Both are
bounded by settings — see [Settings](settings.md) — with sensible defaults
(depth 8, enum 100) that comfortably cover ordinary API designs while
guarding against runaway growth.

## Tool execution reuses your view's existing performance characteristics

`execute_tool` doesn't add its own database queries or duplicate work — it
calls your viewset's real `list`/`create`/`retrieve`/etc. methods via
`.as_view()`, so if you've optimized that view's `get_queryset()`
(`select_related`, `prefetch_related`, pagination, ...), those
optimizations apply exactly the same way whether the request originated
from an LLM tool call or a normal HTTP client. There is nothing
LLM-gateway-specific to additionally optimize on the database side.

## Benchmarking your own tool set

```python
import time
from drf_llm_gateway import to_openai_tools

start = time.perf_counter()
tools = to_openai_tools()
elapsed_ms = (time.perf_counter() - start) * 1000
print(f"Generated {len(tools)} tool schemas in {elapsed_ms:.2f}ms")
```

For execution latency, measure `execute_tool` exactly as you would
measure any other view call (e.g. `django-silk`, APM query-time
dashboards, or a simple `CaptureQueriesContext` around the call).
