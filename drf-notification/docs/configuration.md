# Configuration

## Minimal configuration

```python
# settings.py
INSTALLED_APPS = [..., "drf_notification"]
```

```python
# urls.py
urlpatterns = [path("notifications/", include("drf_notification.urls"))]
```

Everything else below is optional refinement.

## Package settings

Every behavioral option lives under one Django setting, `NOTIFICATIONS`:

```python
NOTIFICATIONS = {
    "BACKENDS": {"sms": "myproject.notifications.TwilioBackend"},
    "RATE_LIMITS": {"email": "20/day"},
    "MAX_RETRIES": 5,
}
```

`BACKENDS` and `RATE_LIMITS` are deep-merged with the defaults - you only
need to specify the channels you want to override. See
[Settings](settings.md) for the full list.

## Registering event types

Register every kind of notification your project sends, ideally in an
`AppConfig.ready()` method so it happens exactly once at startup:

```python
from drf_notification.constants import CHANNEL_EMAIL, CHANNEL_IN_APP
from drf_notification.events import register

register(
    "order.shipped",
    "An order has shipped.",
    default_channels=frozenset({CHANNEL_EMAIL, CHANNEL_IN_APP}),
)
```

## Custom delivery backends

```python
NOTIFICATIONS = {
    "BACKENDS": {
        "sms": "myproject.notifications.backends.TwilioBackend",
        "push": "myproject.notifications.backends.FcmBackend",
    },
}
```

See [Advanced Usage](advanced-usage.md#custom-backends) for the
`NotificationBackend` interface.

## Celery

```bash
pip install drf-notification[celery]
```

```python
NOTIFICATIONS = {"USE_CELERY": True}
```

`drf_notification.tasks` is named so Celery's `app.autodiscover_tasks()`
finds `deliver_notification_task` automatically once
`drf_notification` is in `INSTALLED_APPS`.

## Templates

Templates are optional and database-backed
(`drf_notification.models.NotificationTemplate`), editable via Django
admin. Without one, a plain default derived from the event's
`description` is used - see [Advanced Usage](advanced-usage.md#templates).

## OpenAPI

No custom integration is needed: every view in
`drf_notification.views` is a standard DRF `ModelViewSet`/`APIView`, so
`drf-spectacular`'s automatic schema generation covers them without
additional configuration.
