# Getting Started

## Prerequisites

Python 3.10+, Django 4.2+, Django REST Framework 3.14+, and a Redis
server (standalone or Cluster).

## 1. Install

```bash
pip install drf-ratelimit-plus
```

## 2. Point it at your Redis

```python
# settings.py
RATELIMIT_PLUS = {
    "REDIS_URL": "redis://localhost:6379/3",
}
```

## 3. Add a throttle to a view

```python
from rest_framework import viewsets
from drf_ratelimit_plus import rate_limit, RateLimitHeadersMixin


class ArticleViewSet(RateLimitHeadersMixin, viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    throttle_classes = [
        rate_limit(rate="100/m", algorithm="token_bucket", burst=20, key="user"),
    ]
```

`RateLimitHeadersMixin` is optional — it adds `RateLimit-Limit`/
`RateLimit-Remaining`/`RateLimit-Reset` to every response. Without it, you
still get `429 Too Many Requests` with `Retry-After` on denial (via DRF's
own `Throttled` exception), you just don't get the informational headers
on success.

## 4. Try it

```bash
for i in $(seq 1 25); do
  curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/articles/
done
```

The first 20 (the `burst` capacity) succeed; after that, once the
steady-state rate (100/minute ≈ 1.67/second) is exceeded, you'll start
seeing `429`s, with `Retry-After` telling the client how long to wait.

## Function-based views

```python
from rest_framework.decorators import api_view
from drf_ratelimit_plus import ratelimit


@api_view(["POST"])
@ratelimit(rate="10/m", key="user")
def expensive_action(request):
    ...
```

## Next steps

- [Configuration](configuration.md) — choosing an algorithm and key
  function.
- [Quick Start](quickstart.md) — plan tiers, weighted costs, composed
  keys.
- [Architecture](architecture.md) — how atomicity and Redis Cluster
  compatibility work.
