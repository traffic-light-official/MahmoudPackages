"""Optional Celery task for asynchronous delivery.

Named ``tasks.py`` deliberately so Celery's ``app.autodiscover_tasks()``
finds it automatically once ``drf_notification`` is listed in
``INSTALLED_APPS``. Importing this module requires the ``celery`` extra;
it is never imported at package import time (only lazily, from
:mod:`drf_notification.notify`, when the ``USE_CELERY`` setting is
enabled), so installing this package without Celery works fine as long as
``USE_CELERY`` stays at its default of ``False``.
"""

from __future__ import annotations

from typing import Any

from celery import shared_task

from drf_notification.backends.registry import get_backend
from drf_notification.exceptions import BackendDeliveryError
from drf_notification.models import Notification
from drf_notification.settings import get_setting


@shared_task(bind=True, name="drf_notification.deliver_notification")  # type: ignore[untyped-decorator]
def deliver_notification_task(self: Any, notification_id: int) -> None:
    """Deliver a single notification by primary key, with retry-with-backoff.

    Dispatched by :func:`~drf_notification.notify.notify` when the
    ``USE_CELERY`` setting is enabled. On a
    :class:`~drf_notification.exceptions.BackendDeliveryError`, retries
    with exponential backoff (``RETRY_BACKOFF_SECONDS * 2**attempt``) up
    to ``MAX_RETRIES`` times before leaving the notification in the
    ``failed`` state permanently.

    Args:
        self: The bound task instance, supplied by Celery via ``bind=True``.
        notification_id: Primary key of the notification to deliver.
    """
    notification = Notification.objects.get(pk=notification_id)
    backend = get_backend(notification.channel)
    try:
        backend.send(notification)
    except BackendDeliveryError as exc:
        notification.mark_failed(str(exc))
        max_retries = get_setting("MAX_RETRIES")
        if self.request.retries < max_retries:
            backoff = get_setting("RETRY_BACKOFF_SECONDS")
            raise self.retry(exc=exc, countdown=backoff * (2**self.request.retries)) from exc
    else:
        notification.mark_sent()
