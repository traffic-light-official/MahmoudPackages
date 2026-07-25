"""Delivers via Django's own configured email backend."""

from __future__ import annotations

from django.core.mail import EmailMessage

from drf_notification.backends.base import NotificationBackend
from drf_notification.exceptions import BackendDeliveryError
from drf_notification.models import Notification
from drf_notification.settings import get_setting


class EmailBackend(NotificationBackend):
    """Delivers via :class:`django.core.mail.EmailMessage` and Django's ``EMAIL_BACKEND``."""

    def send(self, notification: Notification) -> None:
        recipient_email = getattr(notification.recipient, "email", None)
        if not recipient_email:
            raise BackendDeliveryError(
                f"User {notification.recipient_id} has no email address on file."
            )

        message = EmailMessage(
            subject=notification.subject,
            body=notification.body,
            from_email=get_setting("FROM_EMAIL"),
            to=[recipient_email],
        )
        try:
            sent_count = message.send(fail_silently=False)
        except Exception as exc:
            raise BackendDeliveryError(str(exc)) from exc
        if sent_count == 0:
            raise BackendDeliveryError("Email backend reported zero messages sent.")
