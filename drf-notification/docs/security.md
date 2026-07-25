# Security

This page covers security considerations specific to
`drf-notification`. For the general vulnerability reporting process, see
[SECURITY.md](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-notification/SECURITY.md).

## Webhook URLs and SSRF

`WebhookTargetSerializer` validates every submitted URL with
`drf_notification.url_safety.validate_public_url()`, which rejects
`localhost`, loopback, private, link-local, reserved, and multicast IP
addresses (including cloud metadata endpoints like
`169.254.169.254`). This is a **best-effort** guard, not a complete SSRF
defense:

- DNS can be re-pointed between validation time and delivery time (a
  time-of-check/time-of-use gap) - a hostname that resolved to a public
  IP when the webhook target was created could resolve to an internal
  address later.
- It does not follow or validate HTTP redirects.
- It only runs at `WebhookTargetSerializer` validation time; if you
  create `WebhookTarget` rows directly (bypassing the serializer), this
  check does not run.

If webhook targets can be supplied by lower-trust users and SSRF is a
serious concern in your deployment, add network-level egress controls
(an allowlisting proxy, or run outbound webhook delivery from a network
segment with no access to internal services) in addition to this guard.

## Webhook payload signing

Every outbound webhook request is signed with HMAC-SHA256 using the
target's own `secret` (a 64-character random hex string, generated with
`secrets.token_hex`, never returned by any serializer field or admin
list display). Verify it on the receiving end using a
constant-time comparison (`hmac.compare_digest`), never `==`, to avoid a
timing side-channel - see
[Advanced Usage](advanced-usage.md#custom-exception-mapping-for-the-webhook-signature).

## Unsubscribe tokens

Single-event unsubscribe tokens are signed with Django's
`TimestampSigner` under a dedicated salt
(`drf_notification.unsubscribe`) and expire after
`UNSUBSCRIBE_TOKEN_MAX_AGE` (default 30 days) - a tampered or expired
token is rejected with `InvalidUnsubscribeTokenError`, never silently
accepted. The persistent preference-center token
(`NotificationSettings.unsubscribe_token`) does not expire by design (it
is meant for a long-lived "manage my notifications" link) but grants
only read access to that one user's own settings/preferences - it
cannot be used to unsubscribe or modify anything (only
`UnsubscribeView`'s signed, expiring token can).

## Notification content

`Notification.body`/`subject` are rendered from a
`NotificationTemplate` (admin-editable, so treat template edit access
the same as any other admin-only capability) or context you provide -
this package does not sanitize or escape template output beyond what
Django's own template engine does by default. Do not interpolate
untrusted user input directly into a template string
(`Template(user_supplied_string)`); only the `context` dict passed to
`notify()` should come from request data, never the template source
itself.

## The `EmailBackend` never logs credentials

Delivery failures are captured via `str(exc)` from the underlying
`django.core.mail` call and stored in `Notification.last_error`; SMTP
credentials are configured via Django's own `EMAIL_*` settings and are
never read, logged, or exposed by this package.

## Dependency security

- Run `pip audit` regularly against your dependency tree.
- Keep Django and Django REST Framework up to date.
- If using Celery, keep it and its broker (Redis/RabbitMQ) patched;
  `deliver_notification_task` accepts only a `notification_id` integer,
  never arbitrary user input, as its task argument.
