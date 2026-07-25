"""Tests for :mod:`drf_notification.async_notify`."""

from __future__ import annotations

import pytest
from django.contrib.auth.models import AbstractUser
from django.test import override_settings

from drf_notification.async_notify import anotify
from drf_notification.constants import CHANNEL_IN_APP
from drf_notification.events import default_registry, register

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def _register_event() -> None:
    register("test.async_event", "An async event.", default_channels=frozenset({CHANNEL_IN_APP}))
    yield
    default_registry.unregister("test.async_event")


class TestAnotify:
    async def test_delivers_and_returns_notifications(self, user: AbstractUser) -> None:
        with override_settings(
            NOTIFICATIONS={
                "BACKENDS": {CHANNEL_IN_APP: "drf_notification.backends.inapp.InAppBackend"}
            }
        ):
            results = await anotify(recipient=user, event_key="test.async_event")

        assert len(results) == 1
        assert results[0].channel == CHANNEL_IN_APP
        assert results[0].status == "sent"
