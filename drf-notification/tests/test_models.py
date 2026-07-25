"""Tests for :mod:`drf_notification.models`."""

from __future__ import annotations

import pytest
from django.contrib.auth.models import AbstractUser
from django.db import IntegrityError

from drf_notification.models import (
    Notification,
    NotificationPreference,
    NotificationSettings,
    WebhookTarget,
)

pytestmark = pytest.mark.django_db


class TestNotificationSettings:
    def test_generates_a_unique_unsubscribe_token(
        self, user: AbstractUser, other_user: AbstractUser
    ) -> None:
        first = NotificationSettings.objects.create(user=user)
        second = NotificationSettings.objects.create(user=other_user)

        assert first.unsubscribe_token != second.unsubscribe_token
        assert len(first.unsubscribe_token) > 20

    def test_has_quiet_hours_false_by_default(self, user: AbstractUser) -> None:
        settings_obj = NotificationSettings.objects.create(user=user)

        assert settings_obj.has_quiet_hours() is False

    def test_has_quiet_hours_true_when_both_bounds_set(self, user: AbstractUser) -> None:
        import datetime as dt

        settings_obj = NotificationSettings.objects.create(
            user=user, quiet_hours_start=dt.time(22, 0), quiet_hours_end=dt.time(7, 0)
        )

        assert settings_obj.has_quiet_hours() is True

    def test_one_settings_row_per_user(self, user: AbstractUser) -> None:
        NotificationSettings.objects.create(user=user)

        with pytest.raises(IntegrityError):
            NotificationSettings.objects.create(user=user)


class TestNotificationPreference:
    def test_unique_per_user_event_channel(self, user: AbstractUser) -> None:
        NotificationPreference.objects.create(user=user, event_key="order.shipped", channel="email")

        with pytest.raises(IntegrityError):
            NotificationPreference.objects.create(
                user=user, event_key="order.shipped", channel="email"
            )

    def test_different_channels_are_independent(self, user: AbstractUser) -> None:
        NotificationPreference.objects.create(user=user, event_key="order.shipped", channel="email")
        NotificationPreference.objects.create(user=user, event_key="order.shipped", channel="sms")


class TestWebhookTarget:
    def test_generates_a_unique_secret(self, user: AbstractUser) -> None:
        first = WebhookTarget.objects.create(user=user, url="https://example.com/hook-a")
        second = WebhookTarget.objects.create(user=user, url="https://example.com/hook-b")

        assert first.secret != second.secret
        assert len(first.secret) >= 32


class TestNotification:
    def test_mark_read_sets_read_at_once(self, user: AbstractUser) -> None:
        notification = Notification.objects.create(recipient=user, event_key="e", channel="in_app")

        assert notification.is_read is False
        notification.mark_read()
        assert notification.is_read is True

        first_read_at = notification.read_at
        notification.mark_read()
        assert notification.read_at == first_read_at

    def test_mark_sent_sets_status_and_timestamp(self, user: AbstractUser) -> None:
        notification = Notification.objects.create(recipient=user, event_key="e", channel="email")

        notification.mark_sent()

        assert notification.status == "sent"
        assert notification.sent_at is not None

    def test_mark_failed_increments_attempts_and_records_error(self, user: AbstractUser) -> None:
        notification = Notification.objects.create(recipient=user, event_key="e", channel="email")

        notification.mark_failed("SMTP timeout")
        notification.mark_failed("SMTP timeout again")

        assert notification.attempts == 2
        assert notification.last_error == "SMTP timeout again"
        assert notification.status == "failed"

    def test_to_context_dict_merges_metadata(self, user: AbstractUser) -> None:
        notification = Notification.objects.create(
            recipient=user,
            event_key="order.shipped",
            channel="email",
            subject="Shipped!",
            context={"order_id": 7},
        )

        merged = notification.to_context_dict()

        assert merged == {"order_id": 7, "event_key": "order.shipped", "subject": "Shipped!"}

    def test_default_ordering_is_newest_first(self, user: AbstractUser) -> None:
        first = Notification.objects.create(recipient=user, event_key="e", channel="email")
        second = Notification.objects.create(recipient=user, event_key="e", channel="email")

        ordered = list(Notification.objects.filter(recipient=user))

        assert ordered[0].pk == second.pk
        assert ordered[1].pk == first.pk
