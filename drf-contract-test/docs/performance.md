# Performance

## Where the time goes

Comparing two schemas is fast — `compare_schemas()` and
`compare_schema_objects()` are pure, in-memory tree walks over
already-parsed dictionaries, bounded by the number of operations and
properties in your API. For APIs with a few hundred endpoints, a full
comparison typically completes in well under a second.

**Generating** a live schema is the expensive step: drf-spectacular has
to introspect every registered view, serializer, and field. This cost is
identical to running `python manage.py spectacular` yourself — this
package adds no overhead on top of drf-spectacular's own generation
time.

## Avoid regenerating the schema per test

If you use the pytest plugin's `contract_schema` fixture, it's
session-scoped: the live schema is generated exactly once per test
session, no matter how many tests request it (directly, or transitively
through `contract_diff`/`contract_cases`). Don't call
`generate_schema()` yourself inside a per-test fixture or a loop — hoist
it to a session-scoped fixture or a module-level constant, as in the
`generate_contract_cases()` + `@pytest.mark.parametrize` pattern in
[Examples](examples.md).

## `$ref` resolution cost

Both `rules._resolve()` (used during comparison) and
`generator._inline_refs()` (used during contract-test validation) walk
`$ref` chains bounded by a fixed maximum depth (`_MAX_RESOLUTION_DEPTH`
/ `_MAX_INLINE_DEPTH`, both 40). This is a safety bound against
malformed or cyclic documents, not a performance tuning knob — real
drf-spectacular schemas resolve in one or two hops. Comparisons
recompute resolution for shared referenced schemas each time they're
encountered rather than caching by ref pointer; for typical API sizes
(low hundreds of distinct component schemas) this hasn't been a
bottleneck in practice, since each resolution is a handful of dict
lookups.

## CLI vs. Python API

The CLI's `compare`/`check` subcommands do the same work as the Python
API — there's no separate, slower code path. Prefer whichever fits your
workflow; there's no performance reason to choose one over the other.

## In CI

The dominant CI cost is almost always Django/DRF app startup (imports,
`django.setup()`), not this package's own logic. If your CI already
pays that cost for your test suite, running `drf-contract-test check`
as a preceding step adds comparatively little on top — schema generation
plus a linear tree walk.
