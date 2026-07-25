"""Resolves a channel to its configured backend instance."""

from __future__ import annotations

from django.utils.module_loading import import_string

from drf_notification.backends.base import NotificationBackend
from drf_notification.settings import get_setting


def get_backend(channel: str) -> NotificationBackend:
    """Return the configured backend instance for ``channel``.

    Args:
        channel: One of the channel constants in
            :mod:`drf_notification.constants`.

    Returns:
        A fresh instance of the
        :class:`~drf_notification.backends.base.NotificationBackend`
        subclass configured for ``channel`` in the ``BACKENDS`` setting.

    Raises:
        KeyError: If ``channel`` has no entry in the ``BACKENDS`` setting.
    """
    backends: dict[str, str] = get_setting("BACKENDS")
    dotted_path = backends[channel]
    backend_class: type[NotificationBackend] = import_string(dotted_path)
    return backend_class()
