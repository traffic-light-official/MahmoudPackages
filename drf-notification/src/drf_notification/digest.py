"""Batches deferred notifications into a single digest per user per channel."""

from __future__ import annotations

from django.db.models import Model

from drf_notification.backends.registry import get_backend
from drf_notification.constants import STATUS_DIGESTED, STATUS_QUEUED_FOR_DIGEST
from drf_notification.exceptions import BackendDeliveryError
from drf_notification.models import Notification, NotificationSettings


def collect_pending_digest_notifications(user: Model) -> dict[str, list[Notification]]:
    """Group a user's queued-for-digest notifications by channel.

    Args:
        user: The recipient whose queue to inspect.

    Returns:
        A dict mapping channel -> list of notifications (creation order),
        for every channel with at least one queued notification.
    """
    # See the note in notify.py: django-stubs resolves the FK to this project's
    # own AUTH_USER_MODEL, which cannot generalize across host-project user models.
    queued = list(
        Notification.objects.filter(  # type: ignore[misc]
            recipient=user, status=STATUS_QUEUED_FOR_DIGEST
        ).order_by("created_at")
    )
    grouped: dict[str, list[Notification]] = {}
    for notification in queued:
        grouped.setdefault(notification.channel, []).append(notification)
    return grouped


def send_digest_for_user(user: Model) -> list[Notification]:
    """Send one combined digest per channel for everything ``user`` has queued.

    Each channel's queued notifications are combined into a single new
    :class:`~drf_notification.models.Notification` row (subject: "Your
    notification digest", body: the concatenation of every queued item's
    subject and body), delivered through that channel's backend, and the
    original queued rows are marked ``digested``.

    Args:
        user: The recipient to send digests for.

    Returns:
        The newly created digest notifications (one per channel that had
        queued items), each already delivered or marked failed.
    """
    grouped = collect_pending_digest_notifications(user)
    digests: list[Notification] = []

    for channel, notifications in grouped.items():
        body = "\n\n".join(f"{n.subject}\n{n.body}".strip() for n in notifications)
        digest = Notification.objects.create(  # type: ignore[misc]
            recipient=user,
            event_key="digest",
            channel=channel,
            subject="Your notification digest",
            body=body,
            context={"notification_ids": [n.pk for n in notifications]},
        )
        digests.append(digest)

        backend = get_backend(channel)
        try:
            backend.send(digest)
        except BackendDeliveryError as exc:
            digest.mark_failed(str(exc))
        else:
            digest.mark_sent()
            Notification.objects.filter(pk__in=[n.pk for n in notifications]).update(
                status=STATUS_DIGESTED
            )

    return digests


def send_due_digests(frequency: str) -> int:
    """Send digests for every user whose ``digest_frequency`` matches ``frequency``.

    Intended to be invoked from a periodic task/management command
    scheduled at the matching cadence (daily/weekly). This function does
    not track *when* a digest was last sent - scheduling cadence is the
    caller's responsibility.

    Args:
        frequency: One of ``"daily"`` or ``"weekly"``.

    Returns:
        The number of users a digest was actually sent for (users with an
        empty queue are skipped and not counted).
    """
    sent_for = 0
    settings_qs = NotificationSettings.objects.filter(digest_frequency=frequency).select_related(
        "user"
    )
    for user_settings in settings_qs:
        if send_digest_for_user(user_settings.user):
            sent_for += 1
    return sent_for
