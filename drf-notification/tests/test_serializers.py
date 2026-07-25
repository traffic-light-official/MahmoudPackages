"""Tests for :mod:`drf_notification.serializers`."""

from __future__ import annotations

import pytest
from django.contrib.auth.models import AbstractUser

from drf_notification.models import WebhookTarget
from drf_notification.serializers import NotificationSerializer, WebhookTargetSerializer
from drf_notification.url_safety import UnsafeWebhookUrlError

pytestmark = pytest.mark.django_db


class TestNotificationSerializer:
    def test_read_only_fields_include_is_read(self, user: AbstractUser) -> None:
        from drf_notification.models import Notification

        notification = Notification.objects.create(
            recipient=user, event_key="e", channel="in_app", subject="s", body="b"
        )

        data = NotificationSerializer(notification).data

        assert data["is_read"] is False
        assert data["event_key"] == "e"


class TestWebhookTargetSerializer:
    def test_rejects_unsafe_url(self) -> None:
        serializer = WebhookTargetSerializer(data={"url": "http://localhost/hook"})

        assert serializer.is_valid() is False
        assert "url" in serializer.errors

    def test_accepts_url_when_resolver_check_passes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def fake_validate(url: str) -> None:
            return None

        monkeypatch.setattr("drf_notification.serializers.validate_public_url", fake_validate)
        serializer = WebhookTargetSerializer(data={"url": "https://example.com/hook"})

        assert serializer.is_valid(), serializer.errors

    def test_create_persists_a_webhook_target(
        self, user: AbstractUser, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("drf_notification.serializers.validate_public_url", lambda url: None)
        serializer = WebhookTargetSerializer(data={"url": "https://example.com/hook"})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(user=user)

        assert isinstance(instance, WebhookTarget)
        assert instance.url == "https://example.com/hook"


def test_unsafe_webhook_url_error_is_a_value_error() -> None:
    assert issubclass(UnsafeWebhookUrlError, ValueError)
