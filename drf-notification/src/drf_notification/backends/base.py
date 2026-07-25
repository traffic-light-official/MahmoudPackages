"""The delivery backend interface every channel backend implements."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from drf_notification.models import Notification


class NotificationBackend(ABC):
    """Base class for a channel delivery backend.

    Subclass this and point the ``BACKENDS`` setting at your subclass to
    plug in a real SMS/push provider (Twilio, Firebase Cloud Messaging,
    etc.) - the shipped defaults for those two channels only log to the
    console.
    """

    @abstractmethod
    def send(self, notification: Notification) -> None:
        """Deliver ``notification``.

        Args:
            notification: The notification to deliver. Its ``subject``
                and ``body`` have already been rendered.

        Raises:
            drf_notification.exceptions.BackendDeliveryError: If delivery
                fails. The caller
                (:func:`~drf_notification.notify.notify`) catches this
                and records the failure for retry; backends should not
                catch it themselves.
        """
        raise NotImplementedError
