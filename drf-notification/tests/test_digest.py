"""Tests for :mod:`drf_notification.digest`."""

from __future__ import annotations

import pytest
from django.contrib.auth.models import AbstractUser
from django.test import override_settings

from drf_notification.digest import (
    collect_pending_digest_notifications,
    send_digest_for_user,
    send_due_digests,
)
from drf_notification.models import Notification, NotificationSettings

pytestmark = pytest.mark.django_db


class TestCollectPendingDigestNotifications:
    def test_groups_by_channel(self, user: AbstractUser) -> None:
        Notification.objects.create(
            recipient=user, event_key="e1", channel="email", status="queued_for_digest"
        )
        Notification.objects.create(
            recipient=user, event_key="e2", channel="email", status="queued_for_digest"
        )
        Notification.objects.create(
            recipient=user, event_key="e3", channel="sms", status="queued_for_digest"
        )
        Notification.objects.create(recipient=user, event_key="e4", channel="email", status="sent")

        grouped = collect_pending_digest_notifications(user)

        assert len(grouped["email"]) == 2
        assert len(grouped["sms"]) == 1

    def test_empty_when_nothing_queued(self, user: AbstractUser) -> None:
        assert collect_pending_digest_notifications(user) == {}


class TestSendDigestForUser:
    def test_sends_one_digest_per_channel_and_marks_originals_digested(
        self, user: AbstractUser
    ) -> None:
        first = Notification.objects.create(
            recipient=user,
            event_key="e1",
            channel="in_app",
            subject="First",
            body="First body",
            status="queued_for_digest",
        )
        second = Notification.objects.create(
            recipient=user,
            event_key="e2",
            channel="in_app",
            subject="Second",
            body="Second body",
            status="queued_for_digest",
        )

        digests = send_digest_for_user(user)

        assert len(digests) == 1
        digest = digests[0]
        assert digest.status == "sent"
        assert "First" in digest.body
        assert "Second" in digest.body

        first.refresh_from_db()
        second.refresh_from_db()
        assert first.status == "digested"
        assert second.status == "digested"

    def test_returns_empty_list_when_nothing_queued(self, user: AbstractUser) -> None:
        assert send_digest_for_user(user) == []

    def test_failed_digest_delivery_does_not_mark_originals_digested(
        self, user: AbstractUser
    ) -> None:
        original = Notification.objects.create(
            recipient=user, event_key="e1", channel="email", status="queued_for_digest"
        )
        user.email = ""
        user.save()

        digests = send_digest_for_user(user)

        assert digests[0].status == "failed"
        original.refresh_from_db()
        assert original.status == "queued_for_digest"


class TestSendDueDigests:
    def test_sends_only_for_matching_frequency(
        self, user: AbstractUser, other_user: AbstractUser
    ) -> None:
        NotificationSettings.objects.create(user=user, digest_frequency="daily")
        NotificationSettings.objects.create(user=other_user, digest_frequency="weekly")
        Notification.objects.create(
            recipient=user, event_key="e", channel="in_app", status="queued_for_digest"
        )
        Notification.objects.create(
            recipient=other_user, event_key="e", channel="in_app", status="queued_for_digest"
        )

        with override_settings(
            NOTIFICATIONS={"BACKENDS": {"in_app": "drf_notification.backends.inapp.InAppBackend"}}
        ):
            sent_for = send_due_digests("daily")

        assert sent_for == 1

    def test_skips_users_with_an_empty_queue(self, user: AbstractUser) -> None:
        NotificationSettings.objects.create(user=user, digest_frequency="daily")

        sent_for = send_due_digests("daily")

        assert sent_for == 0
