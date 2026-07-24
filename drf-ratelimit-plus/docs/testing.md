# Testing

## Running the package's own test suite

```bash
git clone https://github.com/mahmoudgshaker/drf-ratelimit-plus.git
cd drf-ratelimit-plus
pip install -e ".[dev]"
pytest
tox  # full Python/Django compatibility matrix
```

Tests use `fakeredis[lua]` (the `[lua]` extra is required — it provides
Lua scripting emulation via `lupa`, without which `EVAL` isn't supported)
so no real Redis server is needed to run the suite.

## Testing your own rate-limited views

Inject a `client=` explicitly to avoid a real Redis dependency in your
own tests:

```python
import fakeredis
import pytest
from rest_framework.test import APIClient

from drf_ratelimit_plus.client import set_redis_client


@pytest.fixture(autouse=True)
def fake_redis():
    client = fakeredis.FakeRedis()
    set_redis_client(client)
    yield client
    set_redis_client(None)


def test_denies_beyond_the_limit():
    client = APIClient()
    for _ in range(5):
        assert client.get("/articles/").status_code == 200
    assert client.get("/articles/").status_code == 429
```

This works because views that don't pass an explicit `client=` to
`rate_limit()` resolve one via `get_redis_client()` at check time —
`set_redis_client()` overrides what that resolves to.

## Testing an algorithm directly

```python
from drf_ratelimit_plus.algorithms import token_bucket_check
from drf_ratelimit_plus.rates import parse_rate


def test_token_bucket_allows_bursts(fake_redis):
    rate = parse_rate("60/m")
    results = [
        token_bucket_check(fake_redis, "k", rate, burst=10, now=0.0) for _ in range(10)
    ]
    assert all(r.allowed for r in results)
```

Pass `now=` explicitly for deterministic time-dependent assertions (e.g.
testing refill behavior) rather than relying on real wall-clock time.

## Testing concurrency genuinely

Use real `ThreadPoolExecutor` workers against a shared `fakeredis`
instance — see `tests/test_concurrency.py` in this package's own
repository for the pattern, which proves (rather than assumes) that
concurrent requests never collectively exceed the configured limit for
any of the three algorithms.

## Testing plan tiers

```python
from unittest.mock import Mock


def test_pro_tier_gets_a_higher_limit(fake_redis):
    from drf_ratelimit_plus import rate_limit

    throttle_cls = rate_limit(rate={"free": "1/m", "pro": "10/m"}, client=fake_redis)
    request = Mock(user=Mock(is_authenticated=True, pk=1, plan="pro"), META={}, headers={})
    for _ in range(10):
        assert throttle_cls().allow_request(request, None) is True
```

## Testing the `Retry-After` header

```python
def test_retry_after_is_set_on_429(client):
    for _ in range(6):
        response = client.get("/login/")
    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) > 0
```
