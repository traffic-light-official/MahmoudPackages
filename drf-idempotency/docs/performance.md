# Performance

## Overhead per request

Every idempotent request pays for exactly:

1. One fingerprint computation (`sha256` over method + path + body — a
   single-digit-microsecond operation for typical request sizes).
2. One backend round-trip (`acquire_or_get`) — one Redis command, or one
   database `INSERT`/`SELECT` inside a transaction.
3. On completion, one more backend round-trip (`complete`) to store the
   response.

For `RedisBackend`, this is two Redis round-trips total per non-replayed
request (negligible — typically sub-millisecond each on a local/same-AZ
Redis). For `DatabaseBackend`, it's two additional queries against your
primary database per request — worth being aware of on a
very-high-throughput write endpoint, though still small relative to the
actual business-logic queries most such endpoints perform.

A *replayed* request is cheaper than the original: one backend read, no
view execution, no additional database writes from your business logic at
all.

## Redis vs. database backend under load

`RedisBackend` is the better choice once idempotency-record writes become
a meaningful fraction of your primary database's write volume — Redis is
purpose-built for exactly this kind of high-throughput, short-lived
key-value workload, and native TTL means no separate cleanup job
competing for database I/O. See [Configuration](configuration.md#choosing-a-backend).

## Body size and fingerprinting cost

`compute_fingerprint()` hashes the full raw request body. For typical JSON
API payloads (bytes to low kilobytes) this is irrelevant. If your API
accepts very large request bodies on idempotent endpoints, be aware the
fingerprint cost scales with body size — SHA-256 processes on the order of
gigabytes per second on modern hardware, so this remains negligible up to
quite large payloads.

## Lock contention

`LOCK_TTL_SECONDS` bounds how long a request can hold its lock. Under
normal operation, lock hold time equals view execution time — pick a
`LOCK_TTL_SECONDS` comfortably above your view's p99 latency so legitimate
slow requests aren't preempted by a retry before they finish (which would
otherwise briefly present as a spurious `409` to the retry, not data
corruption).

## Benchmarking your own setup

```python
import time
from drf_idempotency.core import get_backend
from datetime import timedelta

backend = get_backend()
start = time.perf_counter()
for i in range(1000):
    backend.acquire_or_get(f"bench-{i}", "fp", lock_ttl=timedelta(seconds=30))
elapsed = time.perf_counter() - start
print(f"{1000 / elapsed:.0f} acquire_or_get calls/sec")
```

Run this against your actual configured backend (and, for `DatabaseBackend`,
your actual production-like database) to get numbers representative of
your deployment rather than generic claims.
