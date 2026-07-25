# Getting Started

## 1. Install

```bash
pip install drf-notification
```

## 2. Add the app

```python
# settings.py
INSTALLED_APPS = [
    ...,
    "drf_notification",
]
```

Run migrations - this package ships models for preferences, settings,
webhook targets, templates, and the notification log itself:

```bash
python manage.py migrate
```

## 3. Wire up the preference-center API (optional but recommended)

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    path("notifications/", include("drf_notification.urls")),
]
```

This gives you, out of the box: `GET/POST /notifications/items/` (list
and mark-read a user's own notifications), `GET/POST /notifications/preferences/`
(per-event opt-in/opt-out), `GET/PATCH /notifications/settings/` (digest
frequency, quiet hours), `POST /notifications/unsubscribe/<token>/`, and
`/notifications/webhook-targets/`.

## 4. Register your event types

```python
# myapp/apps.py
from django.apps import AppConfig


class MyAppConfig(AppConfig):
    name = "myapp"

    def ready(self) -> None:
        from drf_notification.constants import CHANNEL_EMAIL, CHANNEL_IN_APP
        from drf_notification.events import register

        register(
            "order.shipped",
            "An order has shipped.",
            default_channels=frozenset({CHANNEL_EMAIL, CHANNEL_IN_APP}),
        )
```

Registering in `AppConfig.ready()` guarantees it runs exactly once, at
startup, regardless of import order - see
[Troubleshooting](troubleshooting.md#my-custom-event-type-isnt-registered-yet-when-notify-runs).

## 5. Send one

```python
from drf_notification.notify import notify

notify(
    recipient=order.customer,
    event_key="order.shipped",
    context={"order_id": order.id, "tracking_url": order.tracking_url},
)
```

`notify()` resolves the customer's channel preferences, quiet hours, and
digest settings, renders a template (or a sensible default derived from
the event's description), and delivers or queues each channel
automatically.

See [Quick Start](quickstart.md) for a complete worked example including
a custom domain exception, templates, and webhook targets.
