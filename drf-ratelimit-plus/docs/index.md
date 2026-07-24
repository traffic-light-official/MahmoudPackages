# drf-ratelimit-plus

Rate limiting for Django REST Framework that goes beyond DRF's built-in
`UserRateThrottle`/`AnonRateThrottle`: token bucket (with real burst
handling), sliding window, fixed window, weighted request costs, per-plan
rate tiers, and Redis Cluster support — built as real
`rest_framework.throttling.BaseThrottle` subclasses.

## Why this exists

DRF's built-in throttles give you one fixed-window counter, one identity
dimension, and no burst tolerance. This package adds the algorithms and
composability real production APIs need, while staying inside DRF's own
throttle lifecycle — so `Retry-After`, `check_throttles()`, and everything
else DRF users already understand keeps working exactly as documented.

```python
from drf_ratelimit_plus import rate_limit


class ArticleViewSet(viewsets.ModelViewSet):
    throttle_classes = [rate_limit(rate="100/m", algorithm="token_bucket", burst=20, key="user")]
```

## Where to go next

- New to the package? Start with [Getting Started](getting-started.md).
- Choosing an algorithm? See [Configuration](configuration.md).
- Want the full picture of the atomicity guarantees? Read
  [Architecture](architecture.md).
- Something not behaving as expected? Check [Troubleshooting](troubleshooting.md).

## At a glance

| Task | Where |
| --- | --- |
| Rate-limit a class-based view/viewset | [`rate_limit()`](api-reference.md#rate_limit) in `throttle_classes` |
| Rate-limit a function-based view | [`@ratelimit()`](api-reference.md#ratelimit) |
| Add `RateLimit-*` response headers | [`RateLimitHeadersMixin`](api-reference.md#ratelimitheadersmixin) |
| Limit per IP / user / API key / tenant | [`drf_ratelimit_plus.keys`](api-reference.md#keys) |
| Different limits per subscription tier | [`rate={"free": ..., "pro": ...}`](quickstart.md#plan-tiers) |
| Weighted costs for expensive endpoints | [`cost=`](quickstart.md#weighted-costs) |
