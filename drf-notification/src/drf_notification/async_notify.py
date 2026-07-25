"""Async-compatible entry point for :func:`~drf_notification.notify.notify`."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from asgiref.sync import sync_to_async
from django.db.models import Model

from drf_notification.models import Notification
from drf_notification.notify import notify


async def anotify(
    *,
    recipient: Model,
    event_key: str,
    context: dict[str, Any] | None = None,
    channels: Iterable[str] | None = None,
) -> list[Notification]:
    """Async wrapper around :func:`~drf_notification.notify.notify`.

    Runs the (synchronous, ORM-bound) notification pipeline in a worker
    thread via :func:`asgiref.sync.sync_to_async`, so it can be awaited
    from an ``async def`` view or consumer without blocking the event
    loop.

    Args:
        recipient: The user to notify.
        event_key: A key registered via
            :func:`~drf_notification.events.register`.
        context: Template context for rendering the subject/body.
        channels: Channels to attempt, overriding the event type's
            defaults.

    Returns:
        The same result :func:`~drf_notification.notify.notify` returns.
    """
    return await sync_to_async(notify, thread_sensitive=True)(
        recipient=recipient, event_key=event_key, context=context, channels=channels
    )
