# Troubleshooting

## `redis.exceptions.ResponseError: unknown command 'eval'`

**Cause:** using `fakeredis` in tests without its `lua` extra installed —
`fakeredis`'s default install doesn't emulate Lua scripting.

**Fix:** `pip install "fakeredis[lua]"` (this package's own `test` extra
already includes it).

## `429 Too Many Requests` immediately on the very first request

**Cause:** almost always a `burst`/`rate` misconfiguration — e.g.
`burst=0`, or a `cost` higher than the configured `rate`'s count (a
single request can never succeed if its cost exceeds the bucket's total
capacity).

**Fix:** ensure `burst >= cost` for token bucket, and `rate.count >= cost`
generally. Check `docs/configuration.md#weighted-costs` if using a
callable cost.

## `RateLimit-*` headers missing from successful responses

**Cause:** the view doesn't use `RateLimitHeadersMixin` (they're not
added automatically just by using `rate_limit()` in `throttle_classes` —
see [Architecture](architecture.md#why-ratelimitthrottle-subclasses-basethrottle-directly)).

**Fix:** add the mixin, before the DRF base class in the MRO:

```python
class ArticleViewSet(RateLimitHeadersMixin, viewsets.ModelViewSet):
    ...
```

For function-based views, `@ratelimit()` adds headers itself — no mixin
needed there.

## Headers show up but are always `None`/missing on some requests

**Cause:** if you override `get_throttles()` yourself on a view that also
uses `RateLimitHeadersMixin`, make sure your override calls
`super().get_throttles()` (don't replace it entirely) so the mixin's
caching still takes effect — see
[Architecture](architecture.md#why-get_throttles-needs-caching).

## `InvalidRateError: Invalid rate string`

**Cause:** a rate string that doesn't match `"<count>/<period>"`, or an
unrecognized period name.

**Fix:** valid periods are `s`/`sec`/`second`, `m`/`min`/`minute`,
`h`/`hour`, `d`/`day`. `count` must be a positive integer (not a decimal).

## `UnknownTierError` when using plan tiers

**Cause:** the resolved tier name (from `tier_resolver`, or
`request.user.plan` by default) has no entry in your `rate={...}` mapping,
*and* your mapping has no entry for the `DEFAULT_TIER` setting to fall
back to.

**Fix:** either add an entry for every tier your resolver can produce, or
add one for whatever `DEFAULT_TIER` is configured to (`"default"` unless
you've changed it).

## Different Django processes/workers seem to have independent limits

**Cause:** each process resolved a *different* Redis instance/DB — check
`REDIS_URL`/`REDIS_CLIENT` is identical across all your app server
processes (a common mistake: pointing at `localhost` in a
multi-container deployment where each container has its own local
Redis, rather than a shared one).

**Fix:** ensure every process connects to the *same* Redis
instance/Cluster — rate limiting is inherently a cross-process concern,
so a per-process-local Redis defeats the purpose entirely.

## `CROSSSLOT Keys in request don't hash to the same slot`

This should not happen with the built-in algorithms (see
[Architecture](architecture.md#redis-cluster-compatibility)) — if you see
it, you're likely using a custom algorithm or key function that builds
multiple Redis keys per identity without a shared `{}` hash tag. Wrap the
shared identity portion in `{}` as `drf_ratelimit_plus.algorithms.sliding_window_check`
does.
