# Common Patterns

## Registering events from multiple apps

Give each app its own `register()` calls in its own `AppConfig.ready()`,
rather than a single central registry module - this keeps an event
type's definition next to the code that raises it, and avoids import-
order problems since `ready()` for every installed app runs before any
request is handled:

```python
# billing/apps.py
class BillingConfig(AppConfig):
    name = "billing"

    def ready(self) -> None:
        from drf_notification.events import register
        register("invoice.overdue", "An invoice is overdue.", urgent=True)
```

## Notifying a group of users

`notify()` takes exactly one recipient; fan out yourself for a group:

```python
for subscriber in article.author.subscribers.all():
    notify(recipient=subscriber, event_key="article.published", context={"article_id": article.id})
```

For large fan-outs, dispatch each `notify()` call as its own Celery task
rather than looping synchronously in a request:

```python
from myproject.tasks import notify_subscriber_task

for subscriber_id in article.author.subscribers.values_list("id", flat=True):
    notify_subscriber_task.delay(subscriber_id, article.id)
```

## Testing that a notification was sent

```python
from django.core import mail


def test_order_shipped_sends_an_email(user):
    notify(recipient=user, event_key="order.shipped", channels=["email"])

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [user.email]
```

For channels without a Django-native test double (SMS, push, webhook),
register a recording test backend instead of asserting on real network
calls - see [Testing](testing.md#testing-custom-backends).

## Building a frontend preference center

```javascript
async function loadPreferences(token) {
  const response = await fetch(`/notifications/preference-center/${token}/`);
  const { settings, preferences } = await response.json();
  renderQuietHoursForm(settings);
  renderPerEventToggles(preferences);
}
```

```javascript
async function unsubscribeFromEverything(token) {
  await fetch(`/notifications/unsubscribe/${token}/`, { method: "POST" });
}
```

## Suppressing notifications during tests/fixtures

Loading fixture data (e.g. `loaddata`, a factory-driven test setup)
often shouldn't trigger real notifications. Since `notify()` is only
called from your own application code (never automatically by a model
signal), this is naturally opt-in - just don't call `notify()` from
code paths that run during fixture loading.

## Auditing what was actually sent

Every attempted delivery - sent, failed, suppressed, or queued - is a
row in `Notification`. Build a simple audit view:

```python
Notification.objects.filter(event_key="order.shipped", created_at__gte=since).values(
    "channel", "status"
).annotate(count=Count("id"))
```
