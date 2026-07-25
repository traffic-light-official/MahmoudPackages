"""Tests for the optional Celery task in :mod:`drf_notification.tasks`."""

from __future__ import annotations

import pytest

pytest.importorskip("celery")

from django.contrib.auth.models import AbstractUser
from django.test import override_settings

from drf_notification.constants import CHANNEL_IN_APP
from drf_notification.models import Notification
from drf_notification.tasks import deliver_notification_task

pytestmark = pytest.mark.django_db


class TestDeliverNotificationTask:
    def test_delivers_successfully(self, user: AbstractUser) -> None:
        notification = Notification.objects.create(
            recipient=user, event_key="e", channel=CHANNEL_IN_APP
        )

        with override_settings(
            NOTIFICATIONS={
                "BACKENDS": {CHANNEL_IN_APP: "drf_notification.backends.inapp.InAppBackend"}
            }
        ):
            deliver_notification_task.apply(args=[notification.pk]).get()

        notification.refresh_from_db()
        assert notification.status == "sent"

    def test_retries_on_backend_delivery_error_then_gives_up(self, user: AbstractUser) -> None:
        notification = Notification.objects.create(recipient=user, event_key="e", channel="email")
        user.email = ""
        user.save()

        with override_settings(NOTIFICATIONS={"MAX_RETRIES": 0}):
            deliver_notification_task.apply(args=[notification.pk]).get()

        notification.refresh_from_db()
        assert notification.status == "failed"
        assert notification.attempts == 1
