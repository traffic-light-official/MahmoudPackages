# Examples

A runnable example project lives in
[`examples/blog/`](https://github.com/MahmoudGShake/MahmoudPackages/tree/master/drf-notification/examples/blog)
in the repository.

## Immediate email + in-app

```python
notify(
    recipient=user,
    event_key="order.shipped",
    context={"order_id": 42, "tracking_url": "https://example.com/track/42"},
)
```

Two `Notification` rows are created (one per default channel), both
delivered immediately (assuming no quiet hours/digest deferral applies).

## Overriding channels for one call

```python
notify(recipient=user, event_key="order.shipped", channels=["email"])
```

Only the `email` channel is attempted, regardless of the event type's
`default_channels` - still filtered by the user's own preferences.

## A disabled channel is skipped

```python
NotificationPreference.objects.create(
    user=user, event_key="order.shipped", channel="sms", enabled=False
)
notify(recipient=user, event_key="order.shipped")  # no "sms" Notification row at all
```

## Quiet hours defer a non-urgent email

```python
NotificationSettings.objects.create(
    user=user, quiet_hours_start=datetime.time(22, 0), quiet_hours_end=datetime.time(7, 0)
)
# called at 23:00 local time:
results = notify(recipient=user, event_key="order.shipped", channels=["email"])
results[0].status  # "queued_for_digest"
```

## An urgent event bypasses quiet hours

```python
register("security.password_reset", "Password reset requested.", urgent=True)
notify(recipient=user, event_key="security.password_reset", channels=["email"])
# delivered immediately even at 3am
```

## A webhook delivery

```python
WebhookTarget.objects.create(user=user, url="https://example.com/hook")
notify(recipient=user, event_key="order.shipped", channels=["webhook"])
```

```http
POST /hook HTTP/1.1
Content-Type: application/json
X-Notification-Signature: sha256=6c1c...
X-Notification-Event: order.shipped

{"event": "order.shipped", "subject": "...", "body": "...", "context": {"order_id": 42}}
```

## A failed delivery, then a successful retry

```python
notify(recipient=user, event_key="order.shipped", channels=["email"])  # user.email == ""
# Notification.status == "failed", attempts == 1

user.email = "user@example.com"
user.save()
```

```bash
python manage.py retry_failed_notifications
# Notification.status == "sent"
```
