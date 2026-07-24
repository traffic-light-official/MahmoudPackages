# drf-ratelimit-plus

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

Full documentation: <https://mahmoudgshake.github.io/MahmoudPackages/drf-ratelimit-plus/>

- [Getting Started](https://mahmoudgshake.github.io/MahmoudPackages/drf-ratelimit-plus/getting-started)
- [Installation](https://mahmoudgshake.github.io/MahmoudPackages/drf-ratelimit-plus/installation)
- [Configuration](https://mahmoudgshake.github.io/MahmoudPackages/drf-ratelimit-plus/configuration) / [Settings](https://mahmoudgshake.github.io/MahmoudPackages/drf-ratelimit-plus/settings)
- [Quick Start](https://mahmoudgshake.github.io/MahmoudPackages/drf-ratelimit-plus/quickstart)
- [Advanced Usage](https://mahmoudgshake.github.io/MahmoudPackages/drf-ratelimit-plus/advanced-usage)
- [Architecture](https://mahmoudgshake.github.io/MahmoudPackages/drf-ratelimit-plus/architecture)
- [API Reference](https://mahmoudgshake.github.io/MahmoudPackages/drf-ratelimit-plus/api-reference)
- [Examples](https://mahmoudgshake.github.io/MahmoudPackages/drf-ratelimit-plus/examples)
- [Common Patterns](https://mahmoudgshake.github.io/MahmoudPackages/drf-ratelimit-plus/common-patterns)
- [Performance](https://mahmoudgshake.github.io/MahmoudPackages/drf-ratelimit-plus/performance)
- [Security](https://mahmoudgshake.github.io/MahmoudPackages/drf-ratelimit-plus/security)
- [Testing](https://mahmoudgshake.github.io/MahmoudPackages/drf-ratelimit-plus/testing)
- [Deployment](https://mahmoudgshake.github.io/MahmoudPackages/drf-ratelimit-plus/deployment)
- [FAQ](https://mahmoudgshake.github.io/MahmoudPackages/drf-ratelimit-plus/faq)
- [Troubleshooting](https://mahmoudgshake.github.io/MahmoudPackages/drf-ratelimit-plus/troubleshooting)

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-ratelimit-plus/CONTRIBUTING.md).

## License

MIT — see [LICENSE](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-ratelimit-plus/LICENSE).
