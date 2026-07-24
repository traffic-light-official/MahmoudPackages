# Quick Start

## Weighted costs

```python
class BulkImportView(APIView):
    throttle_classes = [
        rate_limit(rate="1000/h", cost=lambda request: len(request.data.get("rows", [1]))),
    ]
```

A request importing 50 rows consumes 50 units from the hourly budget —
proportional to actual cost, not counted as "one request" the same as a
single-row import.

## Plan tiers

```python
class ReportView(APIView):
    throttle_classes = [
        rate_limit(
            rate={"free": "10/h", "pro": "100/h", "enterprise": "unlimited"},
            key="user",
        )
    ]
```

Wait — `"unlimited"` isn't a valid rate string; for an effectively
unlimited tier, use a very high number instead (there's no dedicated
"unlimited" sentinel, keeping the rate format uniform):

```python
rate={"free": "10/h", "pro": "100/h", "enterprise": "1000000/h"}
```

By default, the tier is read from `request.user.plan`. Override with
`tier_resolver=` for any other lookup (a related `Subscription` model, a
JWT claim, ...):

```python
rate_limit(
    rate={"free": "10/h", "pro": "100/h"},
    tier_resolver=lambda request: request.auth.get("plan", "free") if request.auth else "free",
)
```

## Composed keys

```python
from drf_ratelimit_plus import combine

rate_limit(rate="1000/h", key=combine("tenant", "user"))
```

Produces keys like `tenant:acme|user:42` — each user gets an independent
budget, but nested within their tenant's namespace (useful if you also
want a separate, higher-level per-tenant limit using a different
throttle).

## Multiple throttles on one view

```python
class ArticleViewSet(RateLimitHeadersMixin, viewsets.ModelViewSet):
    throttle_classes = [
        rate_limit(rate="1000/h", key="tenant", scope="tenant-wide"),
        rate_limit(rate="100/h", key="user"),
    ]
```

Both are checked; DRF denies the request if *either* throttle denies it.
`RateLimitHeadersMixin` reports the tightest (lowest `remaining`) of the
two in the response headers, since that's the one closest to being hit.

## Custom key functions

```python
def by_organization_and_endpoint(request, view=None):
    org_id = request.user.organization_id
    endpoint = view.__class__.__name__ if view else request.path
    return f"org:{org_id}:{endpoint}"

rate_limit(rate="500/h", key=by_organization_and_endpoint)
```

## Checking a result programmatically

```python
from drf_ratelimit_plus.algorithms import token_bucket_check
from drf_ratelimit_plus.rates import parse_rate
from drf_ratelimit_plus.client import get_redis_client

result = token_bucket_check(get_redis_client(), "my-key", parse_rate("10/m"), burst=10)
print(result.allowed, result.remaining, result.reset_seconds)
```

Useful for building a custom admin dashboard showing current rate-limit
state, or for a pre-flight check before an expensive client-side operation.

## Next steps

- [Advanced Usage](advanced-usage.md) — writing custom key functions,
  combining with authentication, testing.
- [Performance](performance.md) — what each algorithm costs.
