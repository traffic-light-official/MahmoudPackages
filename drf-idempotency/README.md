# drf-idempotency

[![CI](https://github.com/mahmoudgshaker/drf-idempotency/actions/workflows/ci.yml/badge.svg)](https://github.com/mahmoudgshaker/drf-idempotency/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/drf-idempotency.svg)](https://pypi.org/project/drf-idempotency/)
[![Python versions](https://img.shields.io/pypi/pyversions/drf-idempotency.svg)](https://pypi.org/project/drf-idempotency/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Stripe-style `Idempotency-Key` support for Django REST Framework: retry a
`POST`/`PATCH`/`PUT` safely and get back the exact same response, with no
risk of double-processing — even under concurrent retries.

```
POST /payments/ HTTP/1.1
Idempotency-Key: 6f7a1e3e-2c9d-4b1a-9d0a-6a6f2b6b9b3a

{"amount": 2000, "currency": "usd"}
```

Retry the exact same request (same key, same body) as many times as you
like — you get the same `201 Created` response every time, and the
payment is only ever created once.

## Why

Networks fail. Clients time out and retry. Without idempotency keys, a
retried `POST` can create a duplicate resource (a double charge, a
duplicate order). Stripe popularized the `Idempotency-Key` header pattern
to solve this cleanly at the API layer; this package brings the same
guarantees to any Django REST Framework project.

## Features

- **Middleware** for automatic, project-wide idempotency handling, and a
  **decorator** for per-view opt-in.
- **Pluggable storage backends**: Redis (atomic `SET NX`) and database
  (unique-constraint + `get_or_create`), with a documented interface for
  writing your own.
- **Response replay**: byte-for-byte identical status code, headers, and
  body on retry — the view is never re-executed.
- **Race-condition safe**: concurrent requests with the same key never
  both execute the view; the loser gets `409 Conflict` or waits, based on
  configuration.
- **Request fingerprinting**: reusing a key with a *different* request
  body is rejected (`422`) rather than silently replaying the wrong
  response.
- **TTL and automatic cleanup**: Redis keys expire natively; a management
  command cleans up expired database records.
- **Status tracking**: query whether a key is in progress, completed, or
  failed.
- Fully typed, PEP 561 compatible, `mypy --strict` clean.

## Installation

```bash
pip install drf-idempotency
pip install drf-idempotency[redis]  # if using the Redis backend
```

## Quick Start

```python
# settings.py
INSTALLED_APPS = [..., "drf_idempotency"]
MIDDLEWARE = [..., "drf_idempotency.middleware.IdempotencyMiddleware"]

IDEMPOTENCY = {
    "BACKEND": "drf_idempotency.backends.database.DatabaseBackend",
}
```

```bash
python manage.py migrate
```

That's it — every `POST`/`PUT`/`PATCH` request carrying an
`Idempotency-Key` header is now automatically deduplicated.

## Documentation

Full documentation: <https://mahmoudgshaker.github.io/drf-idempotency/>

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
