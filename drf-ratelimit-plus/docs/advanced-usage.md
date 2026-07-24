# Advanced Usage

## Writing a custom key function

Any callable matching `(request, view=None) -> str` works:

```python
def by_client_certificate(request, view=None):
    cert_cn = request.META.get("SSL_CLIENT_S_DN_CN")
    return f"cert:{cert_cn}" if cert_cn else "anonymous"


rate_limit(rate="1000/h", key=by_client_certificate)
```

## Reusable named throttle classes

For a limit you apply to many views, define a named subclass once instead
of repeating `rate_limit(...)` calls — mirroring the pattern DRF's own
`UserRateThrottle` uses:

```python
from drf_ratelimit_plus.throttles import RateLimitThrottle


class StandardUserThrottle(RateLimitThrottle):
    algorithm = "token_bucket"
    rate = "1000/h"
    burst = 100
    key = "user"


class ArticleViewSet(viewsets.ModelViewSet):
    throttle_classes = [StandardUserThrottle]
```

Remember: if you want `rate`/`key`/`cost` to be a callable on a directly
subclassed throttle (rather than via `rate_limit()`), wrap it in
`staticmethod(...)` explicitly — see the note on
[`RateLimitThrottle`](api-reference.md#ratelimitthrottle).

## Combining with authentication-aware permissions

Rate limiting and permissions are independent DRF concepts that compose
naturally — `throttle_classes` and `permission_classes` are both checked
during `initial()`, in the order DRF always uses (authentication, then
permissions, then throttles):

```python
class ArticleViewSet(RateLimitHeadersMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    throttle_classes = [rate_limit(rate="1000/h", key="user")]
```

An unauthenticated request is rejected by the permission check before it
ever reaches the throttle.

## Testing views that use `rate_limit()`

Inject a `client=` directly to avoid touching a real Redis server in
tests — see [Testing](testing.md).

## Building a custom algorithm

The three built-in algorithms are just Python functions taking
`(client, key, rate, *, cost, now) -> LimitResult` — nothing throttle- or
DRF-specific about their signature. Write your own following the same
shape (see `drf_ratelimit_plus.algorithms` for the reference
implementations, especially the Redis Cluster considerations described in
[Architecture](architecture.md)), then wire it into a custom throttle
subclass:

```python
from drf_ratelimit_plus.results import LimitResult
from drf_ratelimit_plus.throttles import RateLimitThrottle


def leaky_bucket_check(client, key, rate, *, cost=1, now=None) -> LimitResult:
    ...


class LeakyBucketThrottle(RateLimitThrottle):
    def allow_request(self, request, view):
        rate = self._resolve_rate(request)
        key = self._build_key(request, view)
        result = leaky_bucket_check(self.client or get_redis_client(), key, rate, cost=self.cost)
        self.last_result = result
        return result.allowed
```

## Inspecting a key's current state directly

```python
from drf_ratelimit_plus.algorithms import token_bucket_check
from drf_ratelimit_plus.client import get_redis_client
from drf_ratelimit_plus.rates import parse_rate

# A read-only "peek" isn't provided directly (every check consumes
# `cost` units) - use cost=0 to inspect without consuming:
result = token_bucket_check(get_redis_client(), "some-key", parse_rate("100/m"), cost=0)
print(result.remaining)
```
