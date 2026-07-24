# Examples

Runnable versions live in
[`examples/`](https://github.com/mahmoudgshaker/drf-ratelimit-plus/tree/main/examples).

## A public API with tiered limits

```python
# views.py
from rest_framework import viewsets
from drf_ratelimit_plus import rate_limit, RateLimitHeadersMixin


class ArticleViewSet(RateLimitHeadersMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    throttle_classes = [
        rate_limit(
            rate={"free": "60/h", "pro": "1000/h"},
            algorithm="token_bucket",
            burst=10,
            key="user",
        ),
    ]
```

```python
# settings.py
RATELIMIT_PLUS = {"REDIS_URL": "redis://localhost:6379/3"}
```

## Per-endpoint limits shared across a viewset's actions

```python
class ArticleViewSet(RateLimitHeadersMixin, viewsets.ModelViewSet):
    throttle_classes = [
        rate_limit(rate="1000/h", scope="article-endpoints"),  # shared across list/retrieve/create/...
    ]
```

## Expensive bulk endpoint with weighted cost

```python
class BulkImportView(RateLimitHeadersMixin, APIView):
    throttle_classes = [
        rate_limit(
            rate="10000/h",
            algorithm="token_bucket",
            burst=1000,
            cost=lambda request: len(request.data.get("rows", [])),
        ),
    ]

    def post(self, request):
        # a request importing 500 rows consumes 500 units
        ...
```

## Client-side handling of 429 + Retry-After

```python
import time
import requests


def call_with_backoff(url, **kwargs):
    while True:
        response = requests.get(url, **kwargs)
        if response.status_code != 429:
            return response
        wait = int(response.headers.get("Retry-After", "1"))
        time.sleep(wait)
```

## Reading the informational headers

```python
response = requests.get("https://api.example.com/articles/")
print(response.headers["RateLimit-Limit"])      # e.g. "1000"
print(response.headers["RateLimit-Remaining"])  # e.g. "997"
print(response.headers["RateLimit-Reset"])      # seconds until reset
```
