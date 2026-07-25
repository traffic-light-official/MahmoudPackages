"""Tests for :mod:`drf_notification.backends`."""

from __future__ import annotations

import json
from http.client import HTTPResponse
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import AbstractUser
from django.core import mail
from django.test import override_settings

from drf_notification.backends.console import ConsoleBackend
from drf_notification.backends.email import EmailBackend
from drf_notification.backends.inapp import InAppBackend
from drf_notification.backends.registry import get_backend
from drf_notification.backends.webhook import WebhookBackend
from drf_notification.constants import WEBHOOK_EVENT_HEADER, WEBHOOK_SIGNATURE_HEADER
from drf_notification.exceptions import BackendDeliveryError
from drf_notification.models import Notification, WebhookTarget

pytestmark = pytest.mark.django_db


class TestConsoleBackend:
    def test_send_logs_and_does_not_raise(
        self, user: AbstractUser, caplog: pytest.LogCaptureFixture
    ) -> None:
        notification = Notification.objects.create(
            recipient=user, event_key="e", channel="sms", subject="Hi", body="Body"
        )

        with caplog.at_level("INFO"):
            ConsoleBackend().send(notification)

        assert "Hi" in caplog.text


class TestInAppBackend:
    def test_send_is_a_no_op(self, user: AbstractUser) -> None:
        notification = Notification.objects.create(recipient=user, event_key="e", channel="in_app")

        assert InAppBackend().send(notification) is None


class TestEmailBackend:
    def test_sends_via_django_mail(self, user: AbstractUser) -> None:
        notification = Notification.objects.create(
            recipient=user, event_key="e", channel="email", subject="Hi", body="Body"
        )

        EmailBackend().send(notification)

        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == "Hi"
        assert mail.outbox[0].to == [user.email]

    def test_raises_when_recipient_has_no_email(self, user: AbstractUser) -> None:
        user.email = ""
        user.save()
        notification = Notification.objects.create(recipient=user, event_key="e", channel="email")

        with pytest.raises(BackendDeliveryError, match="no email address"):
            EmailBackend().send(notification)

    def test_wraps_send_failures(self, user: AbstractUser) -> None:
        notification = Notification.objects.create(
            recipient=user, event_key="e", channel="email", subject="Hi", body="Body"
        )

        with (
            patch("django.core.mail.message.EmailMessage.send", side_effect=OSError("smtp down")),
            pytest.raises(BackendDeliveryError, match="smtp down"),
        ):
            EmailBackend().send(notification)


class TestWebhookBackend:
    def test_raises_when_no_active_targets(self, user: AbstractUser) -> None:
        notification = Notification.objects.create(recipient=user, event_key="e", channel="webhook")

        with pytest.raises(BackendDeliveryError, match="no active webhook targets"):
            WebhookBackend().send(notification)

    def test_ignores_inactive_targets(self, user: AbstractUser) -> None:
        WebhookTarget.objects.create(user=user, url="https://example.com/hook", is_active=False)
        notification = Notification.objects.create(recipient=user, event_key="e", channel="webhook")

        with pytest.raises(BackendDeliveryError, match="no active webhook targets"):
            WebhookBackend().send(notification)

    def test_posts_signed_payload(self, user: AbstractUser) -> None:
        WebhookTarget.objects.create(user=user, url="https://example.com/hook")
        notification = Notification.objects.create(
            recipient=user, event_key="order.shipped", channel="webhook", subject="s", body="b"
        )

        fake_response = MagicMock(spec=HTTPResponse)
        fake_response.status = 200
        fake_response.__enter__ = MagicMock(return_value=fake_response)
        fake_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=fake_response) as urlopen:
            WebhookBackend().send(notification)

        request = urlopen.call_args[0][0]
        # urllib.request.Request.add_header() stores header names via
        # str.capitalize() (first char upper, rest lower); get_header() does
        # NOT normalize its argument, so the lookup key must match exactly.
        signature = request.get_header(WEBHOOK_SIGNATURE_HEADER.capitalize())
        assert signature.startswith("sha256=")
        assert request.get_header(WEBHOOK_EVENT_HEADER.capitalize()) == "order.shipped"
        payload = json.loads(request.data)
        assert payload["event"] == "order.shipped"

    def test_raises_when_target_responds_with_error_status(self, user: AbstractUser) -> None:
        WebhookTarget.objects.create(user=user, url="https://example.com/hook")
        notification = Notification.objects.create(recipient=user, event_key="e", channel="webhook")

        fake_response = MagicMock(spec=HTTPResponse)
        fake_response.status = 500
        fake_response.__enter__ = MagicMock(return_value=fake_response)
        fake_response.__exit__ = MagicMock(return_value=False)

        with (
            patch("urllib.request.urlopen", return_value=fake_response),
            pytest.raises(BackendDeliveryError, match="responded 500"),
        ):
            WebhookBackend().send(notification)

    def test_succeeds_if_at_least_one_target_is_reachable(self, user: AbstractUser) -> None:
        WebhookTarget.objects.create(user=user, url="https://example.com/hook-a")
        WebhookTarget.objects.create(user=user, url="https://example.com/hook-b")
        notification = Notification.objects.create(recipient=user, event_key="e", channel="webhook")

        fake_response = MagicMock(spec=HTTPResponse)
        fake_response.status = 200
        fake_response.__enter__ = MagicMock(return_value=fake_response)
        fake_response.__exit__ = MagicMock(return_value=False)

        import urllib.error

        def side_effect(request: Any, timeout: float) -> Any:
            del timeout
            if "hook-a" in request.full_url:
                raise urllib.error.URLError("connection refused")
            return fake_response

        with patch("urllib.request.urlopen", side_effect=side_effect):
            WebhookBackend().send(notification)


class TestBackendRegistry:
    def test_resolves_configured_backend_class(self) -> None:
        backend = get_backend("in_app")

        assert isinstance(backend, InAppBackend)

    def test_resolves_a_custom_override(self) -> None:
        with override_settings(
            NOTIFICATIONS={
                "BACKENDS": {"sms": "drf_notification.backends.inapp.InAppBackend"},
            }
        ):
            backend = get_backend("sms")

        assert isinstance(backend, InAppBackend)

    def test_unknown_channel_raises_key_error(self) -> None:
        with pytest.raises(KeyError):
            get_backend("carrier_pigeon")
