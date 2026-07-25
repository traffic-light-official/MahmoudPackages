"""Tests for the ``send_digests`` and ``retry_failed_notifications`` management commands."""

from __future__ import annotations

from io import StringIO

import pytest
from django.contrib.auth.models import AbstractUser
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from drf_notification.models import Notification, NotificationSettings

pytestmark = pytest.mark.django_db


class TestSendDigestsCommand:
    def test_sends_digests_for_matching_frequency(self, user: AbstractUser) -> None:
        NotificationSettings.objects.create(user=user, digest_frequency="daily")
        Notification.objects.create(
            recipient=user, event_key="e", channel="in_app", status="queued_for_digest"
        )
        out = StringIO()

        call_command("send_digests", frequency="daily", stdout=out)

        assert "Sent daily digests to 1 user" in out.getvalue()

    def test_invalid_frequency_is_rejected(self) -> None:
        with pytest.raises(CommandError):
            call_command("send_digests", frequency="hourly")


class TestRetryFailedNotificationsCommand:
    def test_retries_eligible_failed_notifications(self, user: AbstractUser) -> None:
        Notification.objects.create(
            recipient=user, event_key="e", channel="in_app", status="failed", attempts=1
        )
        out = StringIO()

        with override_settings(NOTIFICATIONS={"MAX_RETRIES": 3}):
            call_command("retry_failed_notifications", stdout=out)

        assert "Retried 1 failed notification" in out.getvalue()
        notification = Notification.objects.get(event_key="e")
        assert notification.status == "sent"

    def test_does_not_retry_notifications_past_max_retries(self, user: AbstractUser) -> None:
        Notification.objects.create(
            recipient=user, event_key="e", channel="in_app", status="failed", attempts=5
        )
        out = StringIO()

        with override_settings(NOTIFICATIONS={"MAX_RETRIES": 3}):
            call_command("retry_failed_notifications", stdout=out)

        assert "Retried 0 failed notification" in out.getvalue()

    def test_respects_limit_option(self, user: AbstractUser) -> None:
        for i in range(3):
            Notification.objects.create(
                recipient=user, event_key=f"e{i}", channel="in_app", status="failed", attempts=0
            )
        out = StringIO()

        call_command("retry_failed_notifications", limit=2, stdout=out)

        assert "Retried 2 failed notification" in out.getvalue()
