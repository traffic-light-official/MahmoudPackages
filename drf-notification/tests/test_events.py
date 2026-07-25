"""Tests for :mod:`drf_notification.events`."""

from __future__ import annotations

import pytest

from drf_notification.constants import CHANNEL_EMAIL, CHANNEL_IN_APP, CHANNEL_SMS
from drf_notification.events import (
    EventRegistry,
    EventType,
    default_registry,
    get_event_type,
    register,
)


@pytest.fixture
def registry() -> EventRegistry:
    return EventRegistry()


class TestEventType:
    def test_defaults(self) -> None:
        event = EventType(key="test.event", description="A test event.")

        assert event.default_channels == frozenset({CHANNEL_IN_APP})
        assert event.urgent is False

    def test_rejects_unknown_channels(self) -> None:
        with pytest.raises(ValueError, match="unknown default_channels"):
            EventType(
                key="test.event", description="d", default_channels=frozenset({"carrier_pigeon"})
            )

    def test_is_frozen(self) -> None:
        event = EventType(key="test.event", description="d")

        with pytest.raises(Exception):  # noqa: B017 - dataclasses.FrozenInstanceError
            event.key = "other"  # type: ignore[misc]


class TestEventRegistry:
    def test_register_and_get(self, registry: EventRegistry) -> None:
        event = EventType(key="order.shipped", description="Shipped.")
        registry.register(event)

        assert registry.get("order.shipped") is event

    def test_get_returns_none_when_unregistered(self, registry: EventRegistry) -> None:
        assert registry.get("nope") is None

    def test_register_overwrites_existing(self, registry: EventRegistry) -> None:
        first = EventType(key="order.shipped", description="First.")
        second = EventType(key="order.shipped", description="Second.")
        registry.register(first)
        registry.register(second)

        assert registry.get("order.shipped") is second

    def test_unregister(self, registry: EventRegistry) -> None:
        registry.register(EventType(key="order.shipped", description="d"))
        registry.unregister("order.shipped")

        assert registry.get("order.shipped") is None

    def test_unregister_missing_key_is_a_no_op(self, registry: EventRegistry) -> None:
        registry.unregister("does.not.exist")

    def test_all_returns_sorted_by_key(self, registry: EventRegistry) -> None:
        registry.register(EventType(key="zeta.event", description="d"))
        registry.register(EventType(key="alpha.event", description="d"))

        assert [event.key for event in registry.all()] == ["alpha.event", "zeta.event"]


class TestModuleLevelRegister:
    def test_register_writes_to_default_registry(self) -> None:
        event = register(
            "test.module_level",
            "A description.",
            default_channels=frozenset({CHANNEL_EMAIL, CHANNEL_SMS}),
            urgent=True,
        )

        try:
            assert default_registry.get("test.module_level") is event
            assert get_event_type("test.module_level") is event
            assert event.urgent is True
            assert event.default_channels == frozenset({CHANNEL_EMAIL, CHANNEL_SMS})
        finally:
            default_registry.unregister("test.module_level")

    def test_register_default_channels_fallback(self) -> None:
        event = register("test.module_level_default", "A description.")

        try:
            assert event.default_channels == frozenset({CHANNEL_IN_APP})
        finally:
            default_registry.unregister("test.module_level_default")
