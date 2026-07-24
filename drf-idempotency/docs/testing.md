# Testing

## Running the package's own test suite

```bash
git clone https://github.com/mahmoudgshaker/drf-idempotency.git
cd drf-idempotency
pip install -e ".[dev]"
pytest
tox  # full Python/Django compatibility matrix
```

Redis-dependent tests use `fakeredis` by default (no real Redis server
needed) and self-skip a small set of `@pytest.mark.redis`-marked tests
against a real server when `REDIS_URL` is set in the environment.

## Testing views protected by the middleware

```python
import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_retry_does_not_duplicate(client_setup):
    client = APIClient()
    first = client.post("/payments/", {"amount": 100}, format="json", HTTP_IDEMPOTENCY_KEY="k1")
    second = client.post("/payments/", {"amount": 100}, format="json", HTTP_IDEMPOTENCY_KEY="k1")
    assert Payment.objects.count() == 1
    assert second.content == first.content
    assert second.headers["Idempotent-Replayed"] == "true"
```

Note: compare `.content`, not `.data` — a replayed response is a plain
`HttpResponse`, not a DRF `Response`, so `.data` isn't available on it
(this is intentional; see [Architecture](architecture.md)).

## Testing key reuse detection

```python
def test_reuse_with_different_body_is_rejected(client):
    client.post("/payments/", {"amount": 100}, format="json", HTTP_IDEMPOTENCY_KEY="k1")
    response = client.post("/payments/", {"amount": 200}, format="json", HTTP_IDEMPOTENCY_KEY="k1")
    assert response.status_code == 422
```

## Testing concurrent requests genuinely

Use real threads against a thread-safe backend (Redis, or `fakeredis` in
tests) rather than simulating the race sequentially, to actually exercise
the atomicity guarantee:

```python
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import fakeredis
from drf_idempotency.backends.redis import RedisBackend


def test_only_one_concurrent_acquisition_succeeds():
    backend = RedisBackend(client=fakeredis.FakeRedis())

    def attempt(i):
        return backend.acquire_or_get("key", f"fp-{i}", lock_ttl=timedelta(seconds=30)).acquired

    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(attempt, range(20)))

    assert sum(results) == 1
```

See `tests/test_concurrency.py` in this package's own repository for the
full pattern, including why the database backend's atomicity is tested
via sequential-conflict simulation rather than real OS threads (a SQLite
`:memory:` database can't be safely shared across threads the way it can
across a single connection — see the module docstring there).

## Testing a custom backend

Write the same test suite against your backend that
`tests/test_backends_database.py` and `tests/test_backends_redis.py` run
against the built-in ones — `acquire_or_get`'s atomicity is the property
that matters most; test it explicitly with concurrent threads, not just
sequentially.

## Testing exception handling directly

For unit-level coverage of `process_idempotent_request`'s exception path
(which behaves differently under middleware vs. the decorator — see
[Architecture](architecture.md#why-view-exceptions-behave-differently-under-middleware-vs-the-decorator)),
call it directly rather than through a full HTTP request:

```python
from drf_idempotency.core import process_idempotent_request


def test_exception_releases_the_lock(rf):
    request = build_request_with_key("key-1")

    def failing_view():
        raise ValueError("boom")

    with pytest.raises(ValueError):
        process_idempotent_request(request, failing_view)

    assert get_idempotency_status("key-1") is None
```
