# Advanced Usage

## Custom backends

Implement `NotificationBackend.send()` and raise
`BackendDeliveryError` on failure - `notify()` catches it, records the
failure, and leaves the notification eligible for retry:

```python
from drf_notification.backends.base import NotificationBackend
from drf_notification.exceptions import BackendDeliveryError
from drf_notification.models import Notification


class TwilioBackend(NotificationBackend):
    def send(self, notification: Notification) -> None:
        phone_number = getattr(notification.recipient, "phone_number", None)
        if not phone_number:
            raise BackendDeliveryError(f"No phone number for user {notification.recipient_id}.")
        try:
            twilio_client.messages.create(to=phone_number, body=notification.body, from_=FROM_NUMBER)
        except TwilioRestException as exc:
            raise BackendDeliveryError(str(exc)) from exc
```

```python
NOTIFICATIONS = {"BACKENDS": {"sms": "myproject.notifications.TwilioBackend"}}
```

## Templates

Templates are looked up by `(event_key, channel, language)`, falling
back to `language="en"`, then to a plain default derived from the
event's `description`:

```python
from drf_notification.models import NotificationTemplate

NotificationTemplate.objects.create(
    event_key="order.shipped",
    channel="email",
    language="en",
    subject_template="Order #{{ order_id }} has shipped",
    body_template="Your order is on its way! Track it: {{ tracking_url }}",
)
```

Templates use standard Django template syntax and are rendered with the
notification's `context`. Manage them through Django admin (they're
registered automatically) or programmatically, as above.

## Digest scheduling

Non-urgent notifications for a user whose `digest_frequency` is
`"daily"` or `"weekly"` (or who is currently in their quiet hours) are
queued instead of sent immediately. Send the batched digest on your own
schedule (cron, Celery beat, etc.):

```bash
python manage.py send_digests --frequency=daily
```

```python
from drf_notification.digest import send_due_digests

send_due_digests("daily")
```

Each channel's queued notifications for a user are combined into a
single new notification (subject: "Your notification digest") and the
originals are marked `digested`. The `in_app` channel is never
deferred - users always see in-app notifications immediately, since
they're passive by nature.

## Quiet hours

```python
NotificationSettings.objects.filter(user=user).update(
    quiet_hours_start=datetime.time(22, 0),
    quiet_hours_end=datetime.time(7, 0),
    timezone_name="America/New_York",
)
```

Correctly handles a window that wraps past midnight, and converts using
the user's configured timezone (or the project's `TIME_ZONE` if unset).
Marking an event type `urgent=True` at registration time bypasses quiet
hours and digesting entirely.

## Retries

Synchronous (no Celery required):

```bash
python manage.py retry_failed_notifications --limit=100
```

Asynchronous, with exponential backoff, via Celery:

```python
NOTIFICATIONS = {"USE_CELERY": True}
```

## Custom exception mapping for the webhook signature

Verify a webhook payload on the receiving end using the target's
`secret` (never logged, never exposed via the API):

```python
import hashlib
import hmac


def verify_signature(secret: str, payload: bytes, header_value: str) -> bool:
    expected = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header_value)
```

## Async views

```python
from drf_notification.async_notify import anotify


async def publish_article(request):
    ...
    await anotify(recipient=subscriber, event_key="article.published", context={...})
```

## Scoping notifications per API version or tenant

`notify()` takes a plain model instance as `recipient` and has no
global state beyond the event registry and Django settings - safe to
call from any context (sync view, async view, Celery task, management
command, signal handler) without special wiring.
