# Troubleshooting

## `UnknownEventTypeError: Unknown notification event type`

The `event_key` passed to `notify()` was never registered. Check for a
typo, and confirm the module containing your `register()` call is
actually imported - putting it in `AppConfig.ready()` (see
[Getting Started](getting-started.md#4-register-your-event-types))
guarantees it runs at Django startup regardless of import order.

## My custom event type isn't registered yet when `notify()` runs

If you call `register()` at the bottom of a `views.py` or
`serializers.py` module instead of `AppConfig.ready()`, registration
only happens the first time that specific module is imported - which
might be *after* some other code path already tried to call `notify()`
for it (e.g. from a management command or a signal handler that never
imports your views module). Move the `register()` call to
`AppConfig.ready()`.

## No email is actually being sent

1. Confirm `EMAIL_BACKEND` in Django settings points at a real backend
   (not `django.core.mail.backends.console.EmailBackend` or
   `locmem.EmailBackend`, which are development/test-only).
2. Confirm the recipient has a non-empty `email` attribute -
   `EmailBackend` raises `BackendDeliveryError` (visible in
   `Notification.last_error`) rather than silently doing nothing.
3. Check `Notification.status` for that row: `"suppressed"` means a
   rate limit or a global unsubscribe blocked it before the backend ever
   ran; `"queued_for_digest"` means quiet hours or a non-immediate
   digest frequency deferred it; `"failed"` means the backend raised.

## A rate-limit test fails intermittently, or only when run with other tests

The rate limiter is backed by Django's cache framework, which - unlike
the database - is not reset between tests automatically. If your test
suite doesn't clear the cache between tests, an earlier test's calls to
`notify()` for the same user/channel silently count toward a later
test's rate limit. Add an autouse `cache.clear()` fixture - see
[Testing](testing.md#clearing-rate-limit-state-between-tests).

## `ImproperlyConfigured: The 'NOTIFICATIONS' Django setting must be a dict`

`NOTIFICATIONS` must be a `dict`, even if empty: `NOTIFICATIONS = {}`.

## `ImproperlyConfigured: Unknown key(s) in 'NOTIFICATIONS'`

A typo in a setting key. Cross-reference with [Settings](settings.md).

## Webhook target creation always fails with "resolves to a disallowed address"

The URL's hostname resolves to a private/loopback/link-local/reserved
IP address - this is the SSRF guard working as intended (see
[Security](security.md#webhook-urls-and-ssrf)). If you're testing
locally against `http://localhost:8000/hook`, that will always be
rejected; use a public tunneling service (ngrok, etc.) during local
development, or bypass the serializer for internal/trusted targets only.

## Digests never seem to send

`send_digests` sends for users whose `digest_frequency` matches
`--frequency` **and** who currently have queued notifications -
`send_due_digests()` skips (and does not count) users with an empty
queue. Confirm: (1) the user's `NotificationSettings.digest_frequency`
actually matches what you're running, (2) there are `Notification` rows
with `status="queued_for_digest"` for that user, and (3) you're actually
running the command/calling `send_due_digests()` on a schedule - this
package does not send digests on its own.

## Celery task never retries

`deliver_notification_task` only calls `self.retry(...)` when
`self.request.retries < MAX_RETRIES`. If `MAX_RETRIES` is `0` (or you've
already exhausted it), the notification is marked `failed` permanently
on the next failure with no further retry - this is the documented
behavior, not a bug; lower `MAX_RETRIES` back up if you need more
attempts.

## Tests fail with `AppRegistryNotReady`

If you're extending this package and add a new top-level import to
`drf_notification/__init__.py`, make sure it does not transitively
import `drf_notification.models` (or anything that does) - see the
note at the top of that module. Django imports every app's
`__init__.py` before any app's models are ready.
