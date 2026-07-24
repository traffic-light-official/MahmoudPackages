# Deployment

## Version pinning

```
drf-ratelimit-plus>=1.0,<2.0
```

## Supported runtime versions

| Dependency | Supported |
| --- | --- |
| Python | 3.10, 3.11, 3.12, 3.13 |
| Django | 4.2, 5.0, 5.1, 5.2 |
| Django REST Framework | 3.14+ |
| Redis | 2.6+ (Cluster mode supported) |

## Redis sizing

Each active rate-limit identity uses one Redis key (fixed window, token
bucket) or two (sliding window), each holding a handful of bytes/fields.
Memory usage scales with the number of *distinct* identities active
within the relevant TTL window, not with request volume — a busy endpoint
hit by the same 10,000 users repeatedly uses the same 10,000 keys
regardless of how many total requests they send.

## Redis Cluster key design

No special configuration is required on your part — every algorithm's
Redis keys are designed to always land on a single Cluster slot per
identity (a single key for fixed window/token bucket; a hash-tag-wrapped
pair for sliding window). See
[Architecture](architecture.md#redis-cluster-compatibility) for exactly
how.

If you build a **custom** algorithm or key function that touches multiple
Redis keys per identity, wrap the shared identity portion in `{}` yourself
to keep it Cluster-safe — the sliding window implementation in
`drf_ratelimit_plus.algorithms` is a working reference for the pattern.

## Rolling out to an existing API

1. Add rate limiting to a low-traffic or internal endpoint first, with a
   generous limit, to validate the Redis connection and header behavior
   in production.
2. Roll out to public endpoints with `burst` set generously above your
   observed peak legitimate traffic, tightening gradually as you observe
   real `RateLimit-Remaining` values via logging (see
   [Common Patterns](common-patterns.md#monitoring-rate-limit-pressure)).
3. Add `RateLimitHeadersMixin` from the start — the headers cost nothing
   extra to compute (the data is already available from the throttle
   check) and give API consumers visibility into their usage from day
   one.

## Failure mode: Redis unavailable

If Redis is unreachable, `client.eval(...)` raises a connection error
from the underlying `redis` client — this package does not silently
"fail open" (treat every request as allowed) or "fail closed" (deny
everything) on a Redis outage; that decision is left to you, since the
right one depends on your risk tolerance. Wrap throttle checks with your
own fallback if you want specific behavior during a Redis outage:

```python
class ResilientThrottle(RateLimitThrottle):
    def allow_request(self, request, view):
        try:
            return super().allow_request(request, view)
        except Exception:
            # Fail open: don't let a Redis outage take down the whole API.
            # Consider logging/alerting here instead of silently passing.
            return True
```
