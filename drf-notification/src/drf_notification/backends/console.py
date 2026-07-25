"""A logging-only backend, the default for the ``sms`` and ``push`` channels."""

from __future__ import annotations

import logging

from drf_notification.backends.base import NotificationBackend
from drf_notification.models import Notification

logger = logging.getLogger("drf_notification.console")


class ConsoleBackend(NotificationBackend):
    """Logs the notification instead of delivering it anywhere.

    This is the default backend for ``sms`` and ``push``, since this
    package does not bundle a Twilio/Firebase/APNs integration. Replace it
    via the ``BACKENDS`` setting with a real provider-backed backend
    before relying on either channel in production.
    """

    def send(self, notification: Notification) -> None:
        logger.info(
            "[%s] to user_id=%s: %s\n%s",
            notification.channel,
            notification.recipient_id,
            notification.subject,
            notification.body,
        )
