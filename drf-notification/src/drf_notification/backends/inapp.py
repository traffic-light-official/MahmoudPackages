"""The no-op backend for the ``in_app`` channel."""

from __future__ import annotations

from drf_notification.backends.base import NotificationBackend
from drf_notification.models import Notification


class InAppBackend(NotificationBackend):
    """No-op backend for the ``in_app`` channel.

    An in-app notification's delivery *is* its
    :class:`~drf_notification.models.Notification` row - there is nothing
    further to transmit, so this backend does nothing.
    """

    def send(self, notification: Notification) -> None:
        return None
