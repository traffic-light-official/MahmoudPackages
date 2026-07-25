"""The core notification pipeline.

:func:`notify` is the single entry point every project integration calls.
It resolves which channels to attempt (event defaults, filtered by the
recipient's preferences), renders the content, applies rate limiting,
quiet hours, and digest deferral, then either delivers immediately or
hands off to Celery, depending on the ``USE_CELERY`` setting.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from django.db.models import Model

from drf_notification.backends.registry import get_backend
from drf_notification.constants import CHANNEL_IN_APP, DIGEST_IMMEDIATE
from drf_notification.events import get_event_type
from drf_notification.exceptions import BackendDeliveryError, UnknownEventTypeError
from drf_notification.models import Notification, NotificationPreference, NotificationSettings
from drf_notification.quiet_hours import is_within_quiet_hours
from drf_notification.ratelimit import is_rate_limited
from drf_notification.rendering import render_notification
from drf_notification.settings import get_setting


def notify(
    *,
    recipient: Model,
    event_key: str,
    context: dict[str, Any] | None = None,
    channels: Iterable[str] | None = None,
) -> list[Notification]:
    """Send a notification of type ``event_key`` to ``recipient``.

    Args:
        recipient: The user to notify.
        event_key: A key registered via
            :func:`~drf_notification.events.register`.
        context: Template context for rendering the subject/body.
        channels: Channels to attempt, overriding the event type's
            ``default_channels``. Each channel is still filtered by the
            recipient's :class:`~drf_notification.models.NotificationPreference`.

    Returns:
        One :class:`~drf_notification.models.Notification` row per
        attempted channel (including channels ultimately suppressed by a
        rate limit or a global unsubscribe, so callers can inspect why).

    Raises:
        UnknownEventTypeError: If ``event_key`` is not registered.
    """
    event = get_event_type(event_key)
    if event is None:
        raise UnknownEventTypeError(event_key)

    resolved_context = context or {}
    requested_channels = set(channels) if channels is not None else set(event.default_channels)
    enabled_channels = _resolve_enabled_channels(recipient, event_key, requested_channels)
    # django-stubs resolves the user FK to this project's own AUTH_USER_MODEL, which it
    # cannot generalize across the arbitrary host-project user models a reusable app must
    # accept; `recipient: Model` is correct at runtime for any concrete user model.
    user_settings, _ = NotificationSettings.objects.get_or_create(user=recipient)  # type: ignore[misc]

    results: list[Notification] = []
    for channel in sorted(enabled_channels):
        subject, body = render_notification(
            event_key=event_key, channel=channel, context=resolved_context
        )
        notification = Notification.objects.create(  # type: ignore[misc]
            recipient=recipient,
            event_key=event_key,
            channel=channel,
            subject=subject,
            body=body,
            context=resolved_context,
        )
        results.append(notification)

        if user_settings.unsubscribed_all:
            _suppress(notification, "Recipient has unsubscribed from all notifications.")
            continue

        if is_rate_limited(recipient.pk, channel):
            _suppress(notification, "Rate limit exceeded.")
            continue

        if not event.urgent and channel != CHANNEL_IN_APP and _should_defer(user_settings, channel):
            notification.status = "queued_for_digest"
            notification.save(update_fields=["status"])
            continue

        _dispatch(notification)

    return results


def redeliver(notification: Notification) -> None:
    """Reattempt delivery of a previously failed notification, in-process.

    Used by the ``retry_failed_notifications`` management command. Does
    not re-check rate limits, quiet hours, or preferences - those were
    already evaluated when the notification was first created.

    Args:
        notification: The notification to retry.
    """
    _deliver_now(notification)


def _resolve_enabled_channels(
    recipient: Model, event_key: str, requested_channels: set[str]
) -> set[str]:
    preferences = {
        pref.channel: pref.enabled
        for pref in NotificationPreference.objects.filter(  # type: ignore[misc]
            user=recipient, event_key=event_key, channel__in=requested_channels
        )
    }
    return {channel for channel in requested_channels if preferences.get(channel, True)}


def _should_defer(user_settings: NotificationSettings, channel: str) -> bool:
    if is_within_quiet_hours(user_settings):
        return True
    return user_settings.digest_frequency != DIGEST_IMMEDIATE


def _suppress(notification: Notification, reason: str) -> None:
    notification.status = "suppressed"
    notification.last_error = reason
    notification.save(update_fields=["status", "last_error"])


def _dispatch(notification: Notification) -> None:
    if get_setting("USE_CELERY"):
        _dispatch_celery(notification)
        return
    _deliver_now(notification)


def _deliver_now(notification: Notification) -> None:
    backend = get_backend(notification.channel)
    try:
        backend.send(notification)
    except BackendDeliveryError as exc:
        notification.mark_failed(str(exc))
    else:
        notification.mark_sent()


def _dispatch_celery(notification: Notification) -> None:
    # Deliberately deferred: drf_notification.tasks imports celery at module
    # level, and celery is an optional extra. Importing it only here means
    # USE_CELERY=False (the default) never requires celery to be installed.
    from drf_notification.tasks import deliver_notification_task  # noqa: PLC0415

    deliver_notification_task.delay(notification.pk)
