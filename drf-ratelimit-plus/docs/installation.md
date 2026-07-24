# Installation

## Requirements

| Dependency | Supported versions |
| --- | --- |
| Python | 3.10, 3.11, 3.12, 3.13 |
| Django | 4.2, 5.0, 5.1, 5.2 |
| Django REST Framework | 3.14+ |
| Redis | Any version supporting `EVAL` (Redis 2.6+; Cluster mode supported) |

`redis` (the Python client) is a required dependency — this package's
atomicity guarantees depend on Redis's Lua scripting (`EVAL`), so there is
no non-Redis fallback backend (unlike some of this package's siblings,
e.g. `drf-idempotency`, which offers a database backend as an
alternative).

## Standard install

```bash
pip install drf-ratelimit-plus
```

## Django project setup

No `INSTALLED_APPS` entry is required — this package has no models or
migrations.

```python
RATELIMIT_PLUS = {
    "REDIS_URL": "redis://localhost:6379/3",
}
```

## Using Redis Cluster

Pass a pre-built `redis.cluster.RedisCluster` client instead of a URL:

```python
# myapp/redis_setup.py
from redis.cluster import RedisCluster

cluster_client = RedisCluster(host="cluster-node-1", port=6379)
```

```python
RATELIMIT_PLUS = {
    "REDIS_CLIENT": "myapp.redis_setup.cluster_client",
}
```

See [Architecture](architecture.md) for why every algorithm here works
correctly against Cluster without cross-slot errors.

## Verifying the install

```bash
python -c "import drf_ratelimit_plus; print(drf_ratelimit_plus.__version__)"
```

## Upgrading

Check [CHANGELOG.md](https://github.com/mahmoudgshaker/drf-ratelimit-plus/blob/main/CHANGELOG.md)
before upgrading across a major version.
