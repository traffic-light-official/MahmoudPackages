"""Tests for :mod:`drf_notification.rendering`."""

from __future__ import annotations

import pytest

from drf_notification.events import default_registry, register
from drf_notification.exceptions import MissingTemplateError
from drf_notification.models import NotificationTemplate
from drf_notification.rendering import render_notification

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _register_event() -> None:
    register("test.rendering_event", "A test event happened.")
    yield
    default_registry.unregister("test.rendering_event")


class TestRenderNotification:
    def test_falls_back_to_event_description_with_no_template(self) -> None:
        subject, body = render_notification(
            event_key="test.rendering_event", channel="email", context={}
        )

        assert subject == "A test event happened."
        assert body == "A test event happened."

    def test_default_body_includes_context(self) -> None:
        _, body = render_notification(
            event_key="test.rendering_event", channel="email", context={"order_id": 7}
        )

        assert "order_id=7" in body

    def test_uses_database_template_when_present(self) -> None:
        NotificationTemplate.objects.create(
            event_key="test.rendering_event",
            channel="email",
            language="en",
            subject_template="Order {{ order_id }} shipped",
            body_template="Your order {{ order_id }} is on its way.",
        )

        subject, body = render_notification(
            event_key="test.rendering_event", channel="email", context={"order_id": 42}
        )

        assert subject == "Order 42 shipped"
        assert body == "Your order 42 is on its way."

    def test_channel_specific_templates_are_independent(self) -> None:
        NotificationTemplate.objects.create(
            event_key="test.rendering_event",
            channel="sms",
            subject_template="",
            body_template="Order {{ order_id }} shipped.",
        )

        subject, body = render_notification(
            event_key="test.rendering_event", channel="sms", context={"order_id": 42}
        )

        assert subject == ""
        assert body == "Order 42 shipped."

    def test_falls_back_to_english_when_requested_language_missing(self) -> None:
        NotificationTemplate.objects.create(
            event_key="test.rendering_event",
            channel="email",
            language="en",
            subject_template="Hello",
            body_template="Hello body",
        )

        subject, body = render_notification(
            event_key="test.rendering_event", channel="email", context={}, language="fr"
        )

        assert subject == "Hello"
        assert body == "Hello body"

    def test_uses_language_specific_template_when_present(self) -> None:
        NotificationTemplate.objects.create(
            event_key="test.rendering_event",
            channel="email",
            language="fr",
            subject_template="Bonjour",
            body_template="Corps bonjour",
        )

        subject, body = render_notification(
            event_key="test.rendering_event", channel="email", context={}, language="fr"
        )

        assert subject == "Bonjour"
        assert body == "Corps bonjour"

    def test_raises_when_no_template_and_no_event_registered(self) -> None:
        with pytest.raises(MissingTemplateError):
            render_notification(event_key="totally.unregistered", channel="email", context={})
