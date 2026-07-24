# drf-ratelimit-plus

[![CI](https://github.com/mahmoudgshaker/drf-ratelimit-plus/actions/workflows/ci.yml/badge.svg)](https://github.com/mahmoudgshaker/drf-ratelimit-plus/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/drf-ratelimit-plus.svg)](https://pypi.org/project/drf-ratelimit-plus/)
[![Python versions](https://img.shields.io/pypi/pyversions/drf-ratelimit-plus.svg)](https://pypi.org/project/drf-ratelimit-plus/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Rate limiting for Django REST Framework that goes beyond DRF's built-in
`UserRateThrottle`/`AnonRateThrottle`: token bucket (with real burst
handling), sliding window, fixed window, weighted request costs, per-plan
rate tiers, and Redis Cluster support — built as real
`rest_framework.throttling.BaseThrottle` subclasses, so `Retry-After` and
the standard throttle lifecycle work exactly as DRF users already expect.

```python
from drf_ratelimit_plus import rate_limit


class ArticleViewSet(viewsets.ModelViewSet):
    throttle_classes = [rate_limit(rate="100/m", algorithm="token_bucket", burst=20, key="user")]
```

## Why

DRF's built-in throttles give you one fixed-window counter, one identity
dimension (user or IP), and no burst tolerance. Real APIs need more:
smooth burst handling that a fixed window can't provide, different limits
per subscription tier, weighted costs for expensive endpoints, and a
rate-limiting layer that scales horizontally against Redis Cluster
without hot-key problems.

## Features

- **Three algorithms**: token bucket (smooth bursts against a steady
  refill rate), sliding window (approximate, memory-efficient, avoids
  fixed-window boundary bursts), and fixed window (simplest, cheapest).
- **Weighted costs**: `@ratelimit(rate="1000/h", cost=5)` for an
  expensive endpoint sharing a budget with cheaper ones.
- **Plan tiers**: different limits per subscription tier, resolved
  per-request.
- **Redis Cluster ready**: every algorithm's Redis keys are designed for
  single-slot (or hash-tagged) atomic operations, so nothing requires
  cross-slot transactions.
- **Standard rate-limit headers**: `RateLimit-Limit`, `RateLimit-Remaining`,
  `RateLimit-Reset`, and `Retry-After` on `429` — via DRF's own
  `Throttled` exception, so existing error-handling code keeps working.
- **Composable key functions**: per IP, per user, per API key, per
  tenant, per endpoint, or any combination.
- **Dynamic configuration**: rates can be a string, or a callable
  re-evaluated per request (e.g. reading a database-configured limit).
- Fully typed, PEP 561 compatible, `mypy --strict` clean.

## Installation

```bash
pip install drf-ratelimit-plus
```

Requires a Redis server (standalone or Cluster) — see
[`docs/installation.md`](docs/installation.md).

## Quick Start

```python
from drf_ratelimit_plus import rate_limit


class ArticleViewSet(viewsets.ModelViewSet):
    throttle_classes = [
        rate_limit(rate="100/m", algorithm="sliding_window", key="ip"),
    ]
```

Or the decorator form, for function-based views:

```python
from rest_framework.decorators import api_view
from drf_ratelimit_plus import ratelimit


@api_view(["POST"])
@ratelimit(rate="10/m", key="user")
def expensive_action(request):
    ...
```

## Documentation

Full documentation: <https://mahmoudgshaker.github.io/drf-ratelimit-plus/>

- [Getting Started](docs/getting-started.md)
- [Installation](docs/installation.md)
- [Configuration](docs/configuration.md) / [Settings](docs/settings.md)
- [Quick Start](docs/quickstart.md)
- [Advanced Usage](docs/advanced-usage.md)
- [Architecture](docs/architecture.md)
- [API Reference](docs/api-reference.md)
- [Examples](docs/examples.md)
- [Common Patterns](docs/common-patterns.md)
- [Performance](docs/performance.md)
- [Security](docs/security.md)
- [Testing](docs/testing.md)
- [Deployment](docs/deployment.md)
- [FAQ](docs/faq.md)
- [Troubleshooting](docs/troubleshooting.md)

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
