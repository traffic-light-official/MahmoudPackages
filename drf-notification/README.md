# drf-notification

[![PyPI version](https://img.shields.io/pypi/v/drf-notification.svg)](https://pypi.org/project/drf-notification/)
[![Python versions](https://img.shields.io/pypi/pyversions/drf-notification.svg)](https://pypi.org/project/drf-notification/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A complete notification preferences system for Django REST Framework:
multi-channel delivery (email, SMS, push, in-app, webhook), per-event
opt-in/opt-out, digest scheduling, quiet hours, signed unsubscribe links,
rate limiting, retries, and optional Celery/async delivery.

```python
from drf_notification.events import register
from drf_notification.notify import notify
from drf_notification.constants import CHANNEL_EMAIL, CHANNEL_IN_APP

register(
    "order.shipped",
    "An order has shipped.",
    default_channels=frozenset({CHANNEL_EMAIL, CHANNEL_IN_APP}),
)

notify(recipient=order.customer, event_key="order.shipped", context={"order_id": order.id})
```

## Why

Every project eventually needs to notify users, and every project
eventually reinvents the same handful of features badly: a hardcoded
`send_mail()` call with no way for the user to opt out, no digesting (so
users get flooded), no quiet hours, no retry on transient failures, and
no consistent record of what was actually sent. `drf-notification`
provides all of that as one small, well-tested layer on top of Django's
own email backend (and your own SMS/push provider) rather than a
heavyweight, opinionated framework.

## Features

- **Five channels**: email, SMS, push, in-app, and signed webhooks, each
  behind a pluggable `NotificationBackend` you can swap out per channel.
- **Per-event, per-channel opt-in/opt-out**, defaulting to each event
  type's declared `default_channels`.
- **Digest scheduling**: non-urgent notifications batch into a daily or
  weekly digest per user, per channel, instead of arriving one at a time.
- **Quiet hours**: a per-user local-time window (with correct
  past-midnight wraparound) during which non-urgent notifications are
  held for the next digest instead of delivered immediately.
- **Signed, stateless unsubscribe tokens** (single-event or
  everything) plus a persistent preference-center token - no login, no
  extra database table of one-time links.
- **Database-backed, admin-editable templates**, with a plain fallback
  so a new event type works before anyone writes a template.
- **Rate limiting** per channel, a lightweight cache-backed guard against
  runaway over-notification.
- **Retries with exponential backoff**, synchronously via a management
  command or asynchronously via a Celery task.
- **Async-compatible**: `anotify()` runs the pipeline in a worker thread
  so it can be awaited from async views.
- **A best-effort SSRF guard** on user-submitted webhook URLs.
- **DRF ViewSets** for notifications, preferences, webhook targets, and
  settings, plus a ready-to-`include()` `urls.py`.
- **Fully typed**, PEP 561 compatible, `mypy --strict` clean.

## Installation

```bash
pip install drf-notification

# with Celery support
pip install drf-notification[celery]
```

Requires Python 3.10+, Django 4.2+, and Django REST Framework 3.14+.

## Quick Start

```python
# settings.py
INSTALLED_APPS = [
    ...,
    "drf_notification",
]
```

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    path("notifications/", include("drf_notification.urls")),
]
```

```python
# apps.py (or anywhere imported at startup)
from drf_notification.constants import CHANNEL_EMAIL, CHANNEL_IN_APP
from drf_notification.events import register

register(
    "order.shipped",
    "An order has shipped.",
    default_channels=frozenset({CHANNEL_EMAIL, CHANNEL_IN_APP}),
)
```

```python
# somewhere in your order-fulfillment code
from drf_notification.notify import notify

notify(
    recipient=order.customer,
    event_key="order.shipped",
    context={"order_id": order.id, "tracking_url": order.tracking_url},
)
```

That's it - `notify()` resolves the customer's channel preferences,
quiet hours, and digest settings, renders a template (or a sensible
default), and delivers or queues each channel automatically.

See [`docs/quickstart.md`](docs/quickstart.md) and
[`docs/advanced-usage.md`](docs/advanced-usage.md) for custom backends,
Celery, and unsubscribe links.

## Documentation

Full documentation is available at
[Documentation Home Page](https://mahmoudgshake.github.io/MahmoudPackages/drf-notification/), including:

- [Getting Started](https://mahmoudgshake.github.io/MahmoudPackages/drf-notification/getting-started)
- [Installation](https://mahmoudgshake.github.io/MahmoudPackages/drf-notification/installation)
- [Configuration](https://mahmoudgshake.github.io/MahmoudPackages/drf-notification/configuration) / [Settings](https://mahmoudgshake.github.io/MahmoudPackages/drf-notification/settings)
- [Quick Start](https://mahmoudgshake.github.io/MahmoudPackages/drf-notification/quickstart)
- [Advanced Usage](https://mahmoudgshake.github.io/MahmoudPackages/drf-notification/advanced-usage)
- [Architecture](https://mahmoudgshake.github.io/MahmoudPackages/drf-notification/architecture)
- [API Reference](https://mahmoudgshake.github.io/MahmoudPackages/drf-notification/api-reference)
- [Examples](https://mahmoudgshake.github.io/MahmoudPackages/drf-notification/examples)
- [Common Patterns](https://mahmoudgshake.github.io/MahmoudPackages/drf-notification/common-patterns)
- [Performance](https://mahmoudgshake.github.io/MahmoudPackages/drf-notification/performance)
- [Security](https://mahmoudgshake.github.io/MahmoudPackages/drf-notification/security)
- [Testing](https://mahmoudgshake.github.io/MahmoudPackages/drf-notification/testing)
- [Deployment](https://mahmoudgshake.github.io/MahmoudPackages/drf-notification/deployment)
- [FAQ](https://mahmoudgshake.github.io/MahmoudPackages/drf-notification/faq)
- [Troubleshooting](https://mahmoudgshake.github.io/MahmoudPackages/drf-notification/troubleshooting)

## Contributing

Contributions are welcome — see [Contributing](https://mahmoudgshake.github.io/MahmoudPackages/drf-notification/contributing).

## License

MIT — see [LICENSE](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-notification/LICENSE).
