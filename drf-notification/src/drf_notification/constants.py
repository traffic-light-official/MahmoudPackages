"""Shared constants for :mod:`drf_notification`."""

from __future__ import annotations

from typing import Final

#: Delivers an email via Django's configured email backend.
CHANNEL_EMAIL: Final[str] = "email"
#: Delivers an SMS message via a registered SMS backend.
CHANNEL_SMS: Final[str] = "sms"
#: Delivers a push notification via a registered push backend.
CHANNEL_PUSH: Final[str] = "push"
#: Persists a :class:`~drf_notification.models.Notification` row a user
#: reads inside the product itself; never leaves the database.
CHANNEL_IN_APP: Final[str] = "in_app"
#: POSTs a signed JSON payload to a user's registered
#: :class:`~drf_notification.models.WebhookTarget`.
CHANNEL_WEBHOOK: Final[str] = "webhook"

#: Every channel this package knows how to deliver on, in a stable order
#: used for choice fields and the delivery pipeline.
ALL_CHANNELS: Final[tuple[str, ...]] = (
    CHANNEL_EMAIL,
    CHANNEL_SMS,
    CHANNEL_PUSH,
    CHANNEL_IN_APP,
    CHANNEL_WEBHOOK,
)

CHANNEL_CHOICES: Final[tuple[tuple[str, str], ...]] = (
    (CHANNEL_EMAIL, "Email"),
    (CHANNEL_SMS, "SMS"),
    (CHANNEL_PUSH, "Push"),
    (CHANNEL_IN_APP, "In-App"),
    (CHANNEL_WEBHOOK, "Webhook"),
)

#: A notification that has not yet been attempted.
STATUS_PENDING: Final[str] = "pending"
#: Delivered successfully.
STATUS_SENT: Final[str] = "sent"
#: Delivery failed after exhausting retries.
STATUS_FAILED: Final[str] = "failed"
#: Held back (quiet hours or a non-immediate digest preference) for a
#: later digest send rather than delivered immediately.
STATUS_QUEUED_FOR_DIGEST: Final[str] = "queued_for_digest"
#: Included in a digest that has since been sent.
STATUS_DIGESTED: Final[str] = "digested"
#: Not sent at all because the recipient opted out, unsubscribed, or hit
#: their rate limit.
STATUS_SUPPRESSED: Final[str] = "suppressed"

STATUS_CHOICES: Final[tuple[tuple[str, str], ...]] = (
    (STATUS_PENDING, "Pending"),
    (STATUS_SENT, "Sent"),
    (STATUS_FAILED, "Failed"),
    (STATUS_QUEUED_FOR_DIGEST, "Queued for digest"),
    (STATUS_DIGESTED, "Digested"),
    (STATUS_SUPPRESSED, "Suppressed"),
)

#: Every notification is sent right away.
DIGEST_IMMEDIATE: Final[str] = "immediate"
#: Non-urgent notifications are batched into one daily email.
DIGEST_DAILY: Final[str] = "daily"
#: Non-urgent notifications are batched into one weekly email.
DIGEST_WEEKLY: Final[str] = "weekly"

DIGEST_FREQUENCY_CHOICES: Final[tuple[tuple[str, str], ...]] = (
    (DIGEST_IMMEDIATE, "Immediate"),
    (DIGEST_DAILY, "Daily digest"),
    (DIGEST_WEEKLY, "Weekly digest"),
)

#: HTTP header carrying the HMAC-SHA256 signature of a webhook payload,
#: in the same ``sha256=<hex>`` shape GitHub/Stripe webhooks use.
WEBHOOK_SIGNATURE_HEADER: Final[str] = "X-Notification-Signature"
#: HTTP header identifying which notification event triggered the webhook.
WEBHOOK_EVENT_HEADER: Final[str] = "X-Notification-Event"

#: Salt used when signing unsubscribe tokens, distinct from any other use
#: of Django's signing framework in the host project.
UNSUBSCRIBE_SIGNING_SALT: Final[str] = "drf_notification.unsubscribe"
#: The special ``event_key`` meaning "unsubscribe from every event".
UNSUBSCRIBE_ALL_EVENTS: Final[str] = "*"
