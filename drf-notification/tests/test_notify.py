"""Tests for :mod:`drf_notification.notify`."""

from __future__ import annotations

import datetime as dt
from typing import ClassVar
from unittest.mock import patch

import pytest
from django.contrib.auth.models import AbstractUser
from django.test import override_settings

from drf_notification.backends.base import NotificationBackend
from drf_notification.constants import CHANNEL_EMAIL, CHANNEL_IN_APP, CHANNEL_SMS
from drf_notification.events import default_registry, register
from drf_notification.exceptions import BackendDeliveryError, UnknownEventTypeError
from drf_notification.models import Notification, NotificationPreference, NotificationSettings
from drf_notification.notify import notify, redeliver

pytestmark = pytest.mark.django_db


class RecordingBackend(NotificationBackend):
    sent: ClassVar[list[Notification]] = []

    def send(self, notification: Notification) -> None:
        RecordingBackend.sent.append(notification)


class FailingBackend(NotificationBackend):
    def send(self, notification: Notification) -> None:
        raise BackendDeliveryError("simulated failure")


@pytest.fixture(autouse=True)
def _reset_recording_backend() -> None:
    RecordingBackend.sent = []


@pytest.fixture(autouse=True)
def _register_event() -> None:
    register(
        "test.notify_event",
        "Something happened.",
        default_channels=frozenset({CHANNEL_EMAIL, CHANNEL_IN_APP}),
    )
    register(
        "test.urgent_event", "Urgent!", default_channels=frozenset({CHANNEL_EMAIL}), urgent=True
    )
    yield
    default_registry.unregister("test.notify_event")
    default_registry.unregister("test.urgent_event")


def _use_recording_backend(*channels: str):
    backends = dict.fromkeys(channels, "tests.test_notify.RecordingBackend")
    return override_settings(NOTIFICATIONS={"BACKENDS": backends})


class TestNotifyBasics:
    def test_unknown_event_raises(self, user: AbstractUser) -> None:
        with pytest.raises(UnknownEventTypeError):
            notify(recipient=user, event_key="does.not.exist")

    def test_creates_one_notification_per_default_channel(self, user: AbstractUser) -> None:
        with _use_recording_backend(CHANNEL_EMAIL):
            results = notify(recipient=user, event_key="test.notify_event")

        assert {n.channel for n in results} == {CHANNEL_EMAIL, CHANNEL_IN_APP}

    def test_explicit_channels_override_event_defaults(self, user: AbstractUser) -> None:
        with _use_recording_backend(CHANNEL_SMS):
            results = notify(recipient=user, event_key="test.notify_event", channels=[CHANNEL_SMS])

        assert {n.channel for n in results} == {CHANNEL_SMS}

    def test_context_is_stored_on_the_notification(self, user: AbstractUser) -> None:
        with _use_recording_backend(CHANNEL_IN_APP):
            results = notify(
                recipient=user,
                event_key="test.notify_event",
                channels=[CHANNEL_IN_APP],
                context={"order_id": 7},
            )

        assert results[0].context == {"order_id": 7}


class TestPreferences:
    def test_disabled_preference_excludes_the_channel(self, user: AbstractUser) -> None:
        NotificationPreference.objects.create(
            user=user, event_key="test.notify_event", channel=CHANNEL_EMAIL, enabled=False
        )

        with _use_recording_backend(CHANNEL_EMAIL, CHANNEL_IN_APP):
            results = notify(recipient=user, event_key="test.notify_event")

        assert CHANNEL_EMAIL not in {n.channel for n in results}

    def test_no_preference_row_defaults_to_enabled(self, user: AbstractUser) -> None:
        with _use_recording_backend(CHANNEL_EMAIL, CHANNEL_IN_APP):
            results = notify(recipient=user, event_key="test.notify_event")

        assert CHANNEL_EMAIL in {n.channel for n in results}


class TestDelivery:
    def test_successful_delivery_marks_sent(self, user: AbstractUser) -> None:
        with _use_recording_backend(CHANNEL_EMAIL, CHANNEL_IN_APP):
            results = notify(recipient=user, event_key="test.notify_event")

        for notification in results:
            notification.refresh_from_db()
            assert notification.status == "sent"
        assert len(RecordingBackend.sent) == 2

    def test_backend_failure_marks_failed(self, user: AbstractUser) -> None:
        with override_settings(
            NOTIFICATIONS={
                "BACKENDS": {
                    CHANNEL_EMAIL: "tests.test_notify.FailingBackend",
                    CHANNEL_IN_APP: "tests.test_notify.RecordingBackend",
                }
            }
        ):
            results = notify(recipient=user, event_key="test.notify_event")

        email_result = next(n for n in results if n.channel == CHANNEL_EMAIL)
        email_result.refresh_from_db()
        assert email_result.status == "failed"
        assert email_result.attempts == 1
        assert email_result.last_error == "simulated failure"


class TestQuietHoursAndDigest:
    def test_non_urgent_event_deferred_during_quiet_hours(self, user: AbstractUser) -> None:
        NotificationSettings.objects.create(
            user=user, quiet_hours_start=dt.time(0, 0), quiet_hours_end=dt.time(23, 59, 59)
        )

        with _use_recording_backend(CHANNEL_EMAIL, CHANNEL_IN_APP):
            results = notify(recipient=user, event_key="test.notify_event")

        email_result = next(n for n in results if n.channel == CHANNEL_EMAIL)
        assert email_result.status == "queued_for_digest"
        # in_app is never deferred (see test_in_app_channel_never_deferred below),
        # so only the email attempt should have been withheld from the backend.
        assert RecordingBackend.sent == [n for n in results if n.channel == CHANNEL_IN_APP]

    def test_in_app_channel_never_deferred(self, user: AbstractUser) -> None:
        NotificationSettings.objects.create(
            user=user, quiet_hours_start=dt.time(0, 0), quiet_hours_end=dt.time(23, 59, 59)
        )

        with _use_recording_backend(CHANNEL_IN_APP):
            results = notify(recipient=user, event_key="test.notify_event")

        in_app_result = next(n for n in results if n.channel == CHANNEL_IN_APP)
        assert in_app_result.status == "sent"

    def test_urgent_event_bypasses_quiet_hours(self, user: AbstractUser) -> None:
        NotificationSettings.objects.create(
            user=user, quiet_hours_start=dt.time(0, 0), quiet_hours_end=dt.time(23, 59, 59)
        )

        with _use_recording_backend(CHANNEL_EMAIL):
            results = notify(recipient=user, event_key="test.urgent_event")

        assert results[0].status == "sent"

    def test_non_immediate_digest_frequency_defers_non_urgent(self, user: AbstractUser) -> None:
        NotificationSettings.objects.create(user=user, digest_frequency="daily")

        with _use_recording_backend(CHANNEL_EMAIL):
            results = notify(recipient=user, event_key="test.notify_event", channels=["email"])

        assert results[0].status == "queued_for_digest"


class TestSuppression:
    def test_unsubscribed_all_suppresses_every_channel(self, user: AbstractUser) -> None:
        NotificationSettings.objects.create(user=user, unsubscribed_all=True)

        with _use_recording_backend(CHANNEL_EMAIL, CHANNEL_IN_APP):
            results = notify(recipient=user, event_key="test.notify_event")

        assert all(n.status == "suppressed" for n in results)
        assert RecordingBackend.sent == []

    def test_rate_limited_channel_is_suppressed(self, user: AbstractUser) -> None:
        with override_settings(
            NOTIFICATIONS={
                "BACKENDS": {CHANNEL_EMAIL: "tests.test_notify.RecordingBackend"},
                "RATE_LIMITS": {CHANNEL_EMAIL: "1/day"},
            }
        ):
            first = notify(recipient=user, event_key="test.notify_event", channels=[CHANNEL_EMAIL])
            second = notify(recipient=user, event_key="test.notify_event", channels=[CHANNEL_EMAIL])

        assert first[0].status == "sent"
        results = second
        assert results[0].last_error == "Rate limit exceeded."


class TestCeleryDispatch:
    def test_use_celery_dispatches_task_instead_of_sending_directly(
        self, user: AbstractUser
    ) -> None:
        with (
            override_settings(NOTIFICATIONS={"USE_CELERY": True}),
            patch("drf_notification.tasks.deliver_notification_task") as mock_task,
        ):
            results = notify(
                recipient=user, event_key="test.notify_event", channels=[CHANNEL_IN_APP]
            )

        mock_task.delay.assert_called_once_with(results[0].pk)


class TestRedeliver:
    def test_redeliver_reattempts_and_marks_sent(self, user: AbstractUser) -> None:
        notification = Notification.objects.create(
            recipient=user, event_key="e", channel=CHANNEL_IN_APP, status="failed", attempts=1
        )

        redeliver(notification)

        notification.refresh_from_db()
        assert notification.status == "sent"
