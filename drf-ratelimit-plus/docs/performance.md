# Performance

## Cost per request

Every check is exactly **one round trip** to Redis (one `EVAL` call),
regardless of algorithm. There is no separate "read" then "write" —
that's the entire point of using a Lua script. On a local or same-AZ
Redis, this is typically sub-millisecond.

## Algorithm cost comparison

| Algorithm | Redis operations per check | Keys touched |
| --- | --- | --- |
| Fixed window | `INCRBY` + conditional `PEXPIRE` + `PTTL` | 1 |
| Sliding window | 2× `GET` + conditional `INCRBY` + `PEXPIRE` | 2 (same slot) |
| Token bucket | `HMGET` + conditional `HSET` + `PEXPIRE` | 1 |

All three are O(1) — none scale with request volume or history length
(unlike, say, a sorted-set-based "exact" sliding window log, which this
package deliberately avoids in favor of the O(1) approximate counter
approach).

## Multiple throttles multiply round trips

If a view has N throttles in `throttle_classes`, that's N Redis round
trips per request (DRF checks each in turn). Keep the throttle count per
view small — two or three is typical (e.g. one per-user, one per-tenant);
avoid stacking many redundant ones.

## Connection pooling

`get_redis_client()` builds one client (via `redis.Redis.from_url()`) and
caches it for the process lifetime — `redis-py`'s client already manages
a connection pool internally, so this package doesn't add its own pooling
layer on top. For high-concurrency deployments, tune the pool via a
custom client passed through `REDIS_CLIENT`:

```python
import redis

pool = redis.ConnectionPool.from_url("redis://localhost:6379/0", max_connections=50)
client = redis.Redis(connection_pool=pool)
```

```python
RATELIMIT_PLUS = {"REDIS_CLIENT": "myapp.redis_setup.client"}
```

## Benchmarking

```python
import time
from drf_ratelimit_plus.algorithms import token_bucket_check
from drf_ratelimit_plus.rates import parse_rate
from drf_ratelimit_plus.client import get_redis_client

client = get_redis_client()
rate = parse_rate("1000000/h")  # effectively unlimited, for pure latency measurement
start = time.perf_counter()
for i in range(1000):
    token_bucket_check(client, f"bench-{i % 10}", rate, burst=1000000)
elapsed = time.perf_counter() - start
print(f"{1000 / elapsed:.0f} checks/sec")
```

Run this against your actual Redis deployment (not `fakeredis`, which
doesn't reflect real network/serialization overhead) for representative
numbers.
