# drf-notification

A complete notification preferences system for Django REST Framework:
multi-channel delivery (email, SMS, push, in-app, webhook), per-event
opt-in/opt-out, digest scheduling, quiet hours, signed unsubscribe links,
rate limiting, retries, and optional Celery/async delivery.

```python
from drf_notification.notify import notify

notify(recipient=order.customer, event_key="order.shipped", context={"order_id": order.id})
```

## Why this exists

Every project eventually needs to notify users, and every project
eventually reinvents the same handful of features badly: a hardcoded
`send_mail()` with no opt-out, no digesting (so users get flooded), no
quiet hours, no retry on transient failures, and no consistent record of
what was actually sent. `drf-notification` provides all of that as one
small, well-tested layer on top of Django's own email backend (and your
own SMS/push provider), not a heavyweight, opinionated framework.

## Where to go next

- New to the package? Start with [Getting Started](getting-started.md).
- Wiring it into an existing project? See [Installation](installation.md)
  and [Configuration](configuration.md).
- Want the full picture of how it works? Read [Architecture](architecture.md).
- Looking for a specific class or setting? Jump to
  [API Reference](api-reference.md) or [Settings](settings.md).
- Something not behaving as expected? Check [Troubleshooting](troubleshooting.md)
  and the [FAQ](faq.md).

## At a glance

| Task | Where |
| --- | --- |
| Declare a new kind of notification | [`register`](api-reference.md#register) |
| Send a notification | [`notify`](api-reference.md#notify) / [`anotify`](api-reference.md#anotify) |
| Let users opt in/out per channel | [`NotificationPreferenceViewSet`](api-reference.md#notificationpreferenceviewset) |
| One-click unsubscribe links | [`generate_unsubscribe_token`](api-reference.md#generate_unsubscribe_token) |
| Batch non-urgent notifications | [Digest scheduling](advanced-usage.md#digest-scheduling) |
| Quiet a user's phone at night | [Quiet hours](advanced-usage.md#quiet-hours) |
| Plug in a real SMS/push provider | [Custom backends](advanced-usage.md#custom-backends) |
| Change limits, backends, retries | [Settings](settings.md) |
