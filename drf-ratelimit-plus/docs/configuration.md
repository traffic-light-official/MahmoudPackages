# Configuration

## Choosing an algorithm

| | Token bucket | Sliding window | Fixed window |
| --- | --- | --- | --- |
| Burst tolerance | Yes — up to `burst` capacity, refilling continuously | No inherent burst beyond smoothing boundary effects | No — allows up to 2x at window boundaries |
| Precision | Exact | Approximate (weighted estimate) | Exact |
| Memory per identity | One Redis Hash (2 fields) | Two Redis strings (current + previous window) | One Redis string |
| Best for | APIs where occasional bursts are fine but sustained abuse isn't | General-purpose limiting without fixed-window's boundary problem | Simplest, cheapest; fine when boundary bursts don't matter |

Default to `token_bucket` — it's the most flexible (`burst` lets you tune
exactly how much bursting is tolerated) and matches how most real API
rate limiters (including Stripe's and GitHub's) actually behave.

```python
rate_limit(rate="100/m", algorithm="token_bucket", burst=20)
```

Use `sliding_window` if you specifically want to avoid token bucket's
"tokens accumulate while idle" property (e.g. you want a stricter,
smoothed average rather than any burst allowance):

```python
rate_limit(rate="100/m", algorithm="sliding_window")
```

Use `fixed_window` only when you've confirmed the boundary-burst
possibility doesn't matter for your use case (e.g. a very generous limit
where 2x for a moment is inconsequential) — it's marginally cheaper.

## Choosing a key function

```python
rate_limit(key="ip")       # anonymous clients, or IP-based abuse prevention
rate_limit(key="user")     # per authenticated user (falls back to IP if anonymous)
rate_limit(key="api_key")  # per API key header
rate_limit(key="tenant")   # per tenant attribute on the request
rate_limit(key="view")     # per endpoint, shared across all callers
```

Or compose dimensions:

```python
from drf_ratelimit_plus import combine

rate_limit(key=combine("tenant", "user"))  # per-user, scoped within each tenant
```

See [`docs/api-reference.md`](api-reference.md#keys) for the full list and
how to write a custom key function.

## Choosing a scope

By default, each view gets an independent limit (the scope defaults to
the view's dotted class path). Pass `scope=` explicitly to share one limit
across multiple views:

```python
rate_limit(rate="1000/h", scope="expensive-operations")
```

## Weighted costs

```python
rate_limit(rate="1000/h", cost=5)               # every request costs 5
rate_limit(rate="1000/h", cost=lambda request: len(request.data.get("items", [])))
```

## Plan tiers

```python
rate_limit(
    rate={"free": "100/h", "pro": "1000/h", "enterprise": "10000/h"},
    tier_resolver=lambda request: request.user.subscription.plan_name,
)
```

See [Quick Start](quickstart.md#plan-tiers).

## Dynamic configuration

Any of `rate`, `key`, or `cost` can be a callable, re-evaluated on every
request — e.g. reading a database-configured limit:

```python
def dynamic_rate(request):
    return RateLimitConfig.objects.get(endpoint=request.path).rate_string

rate_limit(rate=dynamic_rate)
```

There is no restart required to change behavior this way — the callable
runs fresh on every request.
