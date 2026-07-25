"""Exceptions raised by :mod:`drf_notification`."""

from __future__ import annotations


class NotificationError(Exception):
    """Base class for every exception raised by this package."""


class UnknownEventTypeError(NotificationError):
    """Raised when :func:`~drf_notification.notify.notify` is called with an unregistered key."""

    def __init__(self, event_key: str) -> None:
        self.event_key = event_key
        super().__init__(
            f"Unknown notification event type: {event_key!r}. Register it first via "
            f"drf_notification.events.register()."
        )


class BackendDeliveryError(NotificationError):
    """Raised by a :class:`~drf_notification.backends.base.NotificationBackend` when delivery fails.

    Caught by :func:`~drf_notification.notify.notify`, which records the
    failure on the :class:`~drf_notification.models.Notification` row and
    leaves it eligible for retry rather than propagating to the caller.
    """


class InvalidUnsubscribeTokenError(NotificationError):
    """Raised when an unsubscribe token fails to verify (tampered, expired, or malformed)."""


class MissingTemplateError(NotificationError):
    """Raised when no template (registered default or database override) exists for a channel."""

    def __init__(self, event_key: str, channel: str) -> None:
        self.event_key = event_key
        self.channel = channel
        super().__init__(f"No template found for event {event_key!r} on channel {channel!r}.")
