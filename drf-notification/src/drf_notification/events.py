"""The notification event type registry.

An "event type" (e.g. ``"order.shipped"``, ``"comment.created"``) is a
code-level definition, not a database row: it names a notification your
project can send, the channels it defaults to, and whether it is urgent
enough to bypass quiet hours and digesting. Per-*user* opt-in/opt-out state
for an event type is what :class:`~drf_notification.models.NotificationPreference`
stores in the database.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from drf_notification.constants import ALL_CHANNELS, CHANNEL_IN_APP


@dataclass(frozen=True, slots=True)
class EventType:
    """A registered kind of notification a project can send.

    Attributes:
        key: Stable, unique identifier, e.g. ``"order.shipped"``. Stored
            verbatim on every :class:`~drf_notification.models.Notification`
            row and used to look up preferences and templates.
        description: Human-readable summary, shown in a preference center
            UI and Django admin.
        default_channels: Channels a notification of this type is sent on
            when the recipient has not explicitly configured a preference
            for it.
        urgent: When ``True``, this event type bypasses quiet hours and
            digesting entirely - notifications are always sent
            immediately. Use sparingly (e.g. security alerts,
            password-reset emails).
    """

    key: str
    description: str
    default_channels: frozenset[str] = field(default_factory=lambda: frozenset({CHANNEL_IN_APP}))
    urgent: bool = False

    def __post_init__(self) -> None:
        unknown = self.default_channels - set(ALL_CHANNELS)
        if unknown:
            raise ValueError(
                f"EventType {self.key!r} has unknown default_channels: {sorted(unknown)}."
            )


class EventRegistry:
    """A registry of :class:`EventType` definitions, keyed by ``key``."""

    def __init__(self) -> None:
        self._events: dict[str, EventType] = {}

    def register(self, event: EventType) -> None:
        """Register ``event``, overwriting any existing registration for the same key.

        Args:
            event: The event type to register.
        """
        self._events[event.key] = event

    def get(self, key: str) -> EventType | None:
        """Return the registered :class:`EventType` for ``key``, or ``None``.

        Args:
            key: The event type key to look up.
        """
        return self._events.get(key)

    def unregister(self, key: str) -> None:
        """Remove the registration for ``key``, if any.

        Primarily useful for tests that need to reset registry state.
        """
        self._events.pop(key, None)

    def all(self) -> list[EventType]:
        """Return every registered :class:`EventType`, sorted by key."""
        return sorted(self._events.values(), key=lambda event: event.key)


#: The registry used by default throughout the package.
default_registry = EventRegistry()


def register(
    key: str,
    description: str,
    *,
    default_channels: frozenset[str] | None = None,
    urgent: bool = False,
) -> EventType:
    """Register an event type on the default registry.

    Args:
        key: Stable, unique identifier, e.g. ``"order.shipped"``.
        description: Human-readable summary.
        default_channels: Channels used when the recipient has no
            explicit preference. Defaults to ``{"in_app"}``.
        urgent: Whether this event type bypasses quiet hours/digesting.

    Returns:
        The registered :class:`EventType`.

    Example:
        .. code-block:: python

            from drf_notification.constants import CHANNEL_EMAIL, CHANNEL_IN_APP
            from drf_notification.events import register

            register(
                "order.shipped",
                "An order has shipped.",
                default_channels=frozenset({CHANNEL_EMAIL, CHANNEL_IN_APP}),
            )
    """
    event = EventType(
        key=key,
        description=description,
        default_channels=default_channels or frozenset({CHANNEL_IN_APP}),
        urgent=urgent,
    )
    default_registry.register(event)
    return event


def get_event_type(key: str) -> EventType | None:
    """Return the registered :class:`EventType` for ``key`` from the default registry."""
    return default_registry.get(key)
