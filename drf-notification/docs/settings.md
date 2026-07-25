# Settings

All settings live under a single Django setting, `NOTIFICATIONS`, a dict
merged on top of the defaults below. `BACKENDS` and `RATE_LIMITS` are
deep-merged (only the keys you provide are overridden); every other
setting is replaced wholesale. Unknown keys and wrong-typed values raise
`django.core.exceptions.ImproperlyConfigured` at first access.

```python
NOTIFICATIONS = {
    "MAX_RETRIES": 5,
}
```

## Reference

### `BACKENDS`

- **Type:** `dict[str, str]`
- **Default:** email -> `EmailBackend`, sms/push -> `ConsoleBackend`,
  in_app -> `InAppBackend`, webhook -> `WebhookBackend`

Maps a channel constant to the dotted path of the
[`NotificationBackend`](api-reference.md#notificationbackend) subclass
used to deliver on it.

### `RATE_LIMITS`

- **Type:** `dict[str, str | None]`
- **Default:** `{"email": "50/day", "sms": "10/day", "push": "100/day",
  "webhook": "200/day"}` (no default limit for `in_app`)

Per-channel rate limits as `"count/period"` strings (`period` is one of
`second`, `minute`, `hour`, `day`). Set a channel to `None` to disable
its limit; channels not listed here are unlimited.

### `MAX_RETRIES`

- **Type:** `int`
- **Default:** `3`

Maximum number of delivery attempts (the first attempt plus this many
retries) before a failed notification is left in the `failed` state
permanently.

### `RETRY_BACKOFF_SECONDS`

- **Type:** `int`
- **Default:** `300`

Base delay for exponential retry backoff: attempt *n* is retried after
`RETRY_BACKOFF_SECONDS * 2**(n-1)` seconds (Celery delivery only).

### `DEFAULT_DIGEST_FREQUENCY`

- **Type:** `str`
- **Default:** `"immediate"`

Default `digest_frequency` for newly created
`NotificationSettings` rows. One of `"immediate"`, `"daily"`, `"weekly"`.

### `WEBHOOK_TIMEOUT`

- **Type:** `int | float`
- **Default:** `5.0`

Timeout, in seconds, for outbound webhook HTTP requests.

### `FROM_EMAIL`

- **Type:** `str | None`
- **Default:** `None`

`From` address used by `EmailBackend`. When `None`, falls back to
Django's own `DEFAULT_FROM_EMAIL`.

### `USE_CELERY`

- **Type:** `bool`
- **Default:** `False`

When `True`, `notify()` dispatches delivery through the Celery task
`deliver_notification_task` instead of sending synchronously in-process.
Requires the `celery` extra and a configured Celery app.

### `UNSUBSCRIBE_TOKEN_MAX_AGE`

- **Type:** `int`
- **Default:** `2592000` (30 days)

Maximum age, in seconds, of a signed single-event unsubscribe link. The
persistent "unsubscribe from everything" link
(`NotificationSettings.unsubscribe_token`) never expires.
