# Performance

## Cost per `notify()` call

For each attempted channel, `notify()` performs:

- One `NotificationPreference` query (filtered to the requested
  channels, via `channel__in`), shared across all channels in a single
  call.
- One `NotificationSettings.objects.get_or_create()` (a single query on
  the common path where settings already exist).
- One template lookup (`NotificationTemplate`, filtered by event/channel/
  language) per channel, or zero queries if you rely on the plain
  fallback.
- One `Notification.objects.create()` per channel.
- Zero or one backend `.send()` call per channel (skipped entirely for
  suppressed/deferred channels).
- One cache read/write for rate limiting, if a limit is configured for
  that channel (`RATE_LIMITS`), using `cache.add()` + `cache.incr()` -
  two fast, non-blocking cache operations, no database I/O.

None of this scales with the number of *registered* event types or the
number of *other* users - it is O(number of channels attempted) per
call, which is at most 5.

## Fan-out

`notify()` is a single-recipient function by design (see
[Architecture](architecture.md)). Fanning out to many recipients (e.g.
"notify every subscriber") means one `notify()` call - and therefore one
round of the queries above - per recipient. For large fan-outs (hundreds
or more), dispatch each call as its own Celery task rather than looping
synchronously in a request/response cycle; see
[Common Patterns](common-patterns.md#notifying-a-group-of-users).

## Digest generation

`send_digest_for_user()` does one query to collect queued notifications
(indexed on `(recipient, channel, status)`), groups them in Python, and
issues one `Notification.objects.create()` and one backend `.send()` per
channel with queued items - not per queued notification. `send_due_digests()`
adds one query to find users with the target `digest_frequency`
(`select_related("user")` avoids an extra query per user for the
recipient lookup inside `send_digest_for_user()`).

## Webhook delivery

Each `WebhookBackend.send()` call is synchronous and blocks for up to
`WEBHOOK_TIMEOUT` seconds per target (default 5s), sequentially across a
user's targets. If a user has many webhook targets and low latency
matters, deliver via Celery (`USE_CELERY = True`) so a slow/unreachable
target doesn't hold up the request/response cycle.

## Indexes

`Notification` is indexed on `(recipient, channel, status)` (the shape
every status-filtered query in this package uses:
`collect_pending_digest_notifications`, `retry_failed_notifications`)
and `(recipient, event_key)` (for per-event history lookups).
`NotificationPreference` is indexed on `(user, event_key)`.
