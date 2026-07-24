"""Resolving the Redis client used by the built-in throttles.

Works with both a standalone :class:`redis.Redis` and
:class:`redis.cluster.RedisCluster` — every algorithm in this package is
designed so its Redis operations touch only a single key (or a small set
of keys sharing a hash tag), so no code here needs to know or care which
kind of client it was given.
"""

from __future__ import annotations

from typing import Any

import redis
from django.test.signals import setting_changed
from django.utils.module_loading import import_string

from drf_ratelimit_plus.settings import get_setting

_client: Any | None = None


def get_redis_client() -> Any:
    """Return the configured Redis client, constructing it on first use.

    Resolution order:

    1. If the ``REDIS_CLIENT`` setting is set, import it — it may be a
       dotted path to a client instance, or to a no-argument callable
       returning one.
    2. Otherwise, build a new :class:`redis.Redis` from the ``REDIS_URL``
       setting.

    The result is cached for the lifetime of the process (invalidated
    automatically if ``RATELIMIT_PLUS`` changes, e.g. via
    ``@override_settings`` in tests).

    Returns:
        A Redis client (standalone or Cluster) implementing at least
        ``.eval()``.
    """
    global _client
    if _client is None:
        dotted_path = get_setting("REDIS_CLIENT")
        if dotted_path:
            candidate = import_string(dotted_path)
            _client = candidate() if callable(candidate) else candidate
        else:
            _client = redis.Redis.from_url(get_setting("REDIS_URL"))
    return _client


def set_redis_client(client: Any | None) -> None:
    """Override the cached client directly (primarily for tests).

    Args:
        client: The client to use for subsequent calls to
            :func:`get_redis_client`, or ``None`` to clear the cache and
            force it to be rebuilt from settings on next use.
    """
    global _client
    _client = client


def _reset_client(*, sender: Any, setting: str, **kwargs: Any) -> None:
    if setting == "RATELIMIT_PLUS":
        set_redis_client(None)


setting_changed.connect(_reset_client)
