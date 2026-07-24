# Common Patterns

## Public API + internal API with different limits

```python
class PublicArticleViewSet(RateLimitHeadersMixin, viewsets.ReadOnlyModelViewSet):
    throttle_classes = [rate_limit(rate="60/h", key="ip")]


class InternalArticleViewSet(RateLimitHeadersMixin, viewsets.ModelViewSet):
    permission_classes = [IsInternalService]
    throttle_classes = [rate_limit(rate="100000/h", key="api_key")]
```

## Login/auth endpoints: strict per-IP limiting

Brute-force protection on authentication endpoints benefits from a tight,
IP-scoped fixed or sliding window (no burst allowance, since burst
tolerance is exactly what an attacker wants):

```python
class LoginView(APIView):
    throttle_classes = [
        rate_limit(rate="5/m", algorithm="fixed_window", key="ip"),
    ]
```

## Webhook receivers: generous limits, cost-weighted by payload size

```python
class WebhookView(APIView):
    throttle_classes = [
        rate_limit(
            rate="100000/h",
            algorithm="token_bucket",
            burst=5000,
            key="api_key",
            cost=lambda request: max(1, len(request.body) // 1024),  # ~1 unit per KB
        ),
    ]
```

## Read-heavy vs. write-heavy limits on the same viewset

```python
class ArticleViewSet(RateLimitHeadersMixin, viewsets.ModelViewSet):
    def get_throttles(self):
        if self.request.method in ("GET", "HEAD"):
            return [rate_limit(rate="1000/h", key="user")()]
        return [rate_limit(rate="50/h", key="user", algorithm="fixed_window")()]
```

## Global default + per-view override

```python
# A shared default throttle used across most views:
DefaultThrottle = rate_limit(rate="1000/h", key="user")

class ArticleViewSet(RateLimitHeadersMixin, viewsets.ModelViewSet):
    throttle_classes = [DefaultThrottle]

class ReportGenerationView(RateLimitHeadersMixin, APIView):
    # A stricter override for one expensive endpoint:
    throttle_classes = [rate_limit(rate="10/h", key="user")]
```

## Multi-tenant SaaS: per-tenant AND per-user limits together

```python
class ArticleViewSet(RateLimitHeadersMixin, viewsets.ModelViewSet):
    throttle_classes = [
        rate_limit(rate="10000/h", key="tenant", scope="tenant-budget"),
        rate_limit(rate="500/h", key=combine("tenant", "user")),
    ]
```

A single heavy user can't exceed their own per-user limit, and no
combination of users within one tenant can exceed that tenant's overall
budget.

## Monitoring rate-limit pressure

Log whenever `RateLimit-Remaining` drops below a threshold, to catch
clients approaching their limit before they start seeing `429`s:

```python
class LoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        remaining = response.headers.get("RateLimit-Remaining")
        if remaining is not None and int(remaining) < 5:
            logger.warning("Client %s nearing rate limit (%s left)", request.user, remaining)
        return response
```
