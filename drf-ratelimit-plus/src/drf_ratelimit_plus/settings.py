"""Django settings integration for :mod:`drf_ratelimit_plus`.

All configuration lives under a single Django setting, ``RATELIMIT_PLUS``,
a dictionary of overrides merged on top of :data:`DEFAULTS`. See
``docs/settings.md`` for the description of every key.
"""

from __future__ import annotations

from typing import Any, Final

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test.signals import setting_changed
from django.utils.functional import cached_property

USER_SETTINGS_NAME: Final[str] = "RATELIMIT_PLUS"

DEFAULTS: Final[dict[str, Any]] = {
    #: A ``redis://`` URL used to construct the default Redis client when
    #: no explicit client is passed to a throttle. Ignored if ``REDIS_CLIENT``
    #: is set.
    "REDIS_URL": "redis://localhost:6379/0",
    #: A dotted path to a pre-built ``redis.Redis`` or
    #: ``redis.cluster.RedisCluster`` instance (or a no-argument callable
    #: returning one) to reuse instead of constructing a new client from
    #: ``REDIS_URL``. ``None`` means "build one from REDIS_URL".
    "REDIS_CLIENT": None,
    #: Prefix applied to every Redis key this package writes.
    "KEY_PREFIX": "ratelimit-plus:",
    #: Response header names. Override if they collide with something
    #: else in your stack.
    "LIMIT_HEADER": "RateLimit-Limit",
    "REMAINING_HEADER": "RateLimit-Remaining",
    "RESET_HEADER": "RateLimit-Reset",
    #: Header name used by the built-in ``by_api_key`` key function.
    "API_KEY_HEADER": "X-API-Key",
    #: Attribute name used by the built-in ``by_tenant`` key function to
    #: read the current tenant off ``request``.
    "TENANT_ATTR": "tenant_id",
    #: Default plan name used by tier resolution when a request has no
    #: identifiable plan (e.g. an anonymous user).
    "DEFAULT_TIER": "default",
}

_TYPE_CHECKS: Final[dict[str, type | tuple[type, ...]]] = {
    "REDIS_URL": str,
    "REDIS_CLIENT": (str, type(None)),
    "KEY_PREFIX": str,
    "LIMIT_HEADER": str,
    "REMAINING_HEADER": str,
    "RESET_HEADER": str,
    "API_KEY_HEADER": str,
    "TENANT_ATTR": str,
    "DEFAULT_TIER": str,
}


class _RateLimitPlusSettings:
    """Lazily-evaluated, validated, cache-invalidating settings object."""

    def __init__(self) -> None:
        setting_changed.connect(self._on_setting_changed)

    @cached_property
    def _user_settings(self) -> dict[str, Any]:
        raw = getattr(settings, USER_SETTINGS_NAME, {})
        if not isinstance(raw, dict):
            raise ImproperlyConfigured(
                f"The '{USER_SETTINGS_NAME}' Django setting must be a dict, "
                f"got {type(raw).__name__}."
            )
        unknown_keys = set(raw) - set(DEFAULTS)
        if unknown_keys:
            raise ImproperlyConfigured(
                f"Unknown key(s) in '{USER_SETTINGS_NAME}': {sorted(unknown_keys)}. "
                f"Valid keys are: {sorted(DEFAULTS)}."
            )
        merged = {**DEFAULTS, **raw}
        for key, expected_type in _TYPE_CHECKS.items():
            if not isinstance(merged[key], expected_type):
                raise ImproperlyConfigured(
                    f"'{USER_SETTINGS_NAME}[\"{key}\"]' must be of type "
                    f"{expected_type}, got {type(merged[key]).__name__}."
                )
        if not merged["KEY_PREFIX"]:
            raise ImproperlyConfigured(f"'{USER_SETTINGS_NAME}[\"KEY_PREFIX\"]' must not be empty.")
        return merged

    def __getitem__(self, key: str) -> Any:
        if key not in DEFAULTS:
            raise KeyError(f"Invalid setting: {key!r}. Valid keys are: {sorted(DEFAULTS)}.")
        return self._user_settings[key]

    def _on_setting_changed(self, *, sender: Any, setting: str, **kwargs: Any) -> None:
        if setting == USER_SETTINGS_NAME:
            self.__dict__.pop("_user_settings", None)


app_settings = _RateLimitPlusSettings()


def get_setting(key: str) -> Any:
    """Return the effective value of a single package setting.

    Args:
        key: One of the keys documented in :data:`DEFAULTS`.

    Returns:
        The user-configured value if present in the ``RATELIMIT_PLUS``
        Django setting, otherwise the default.

    Raises:
        KeyError: If ``key`` is not a recognized setting name.
        django.core.exceptions.ImproperlyConfigured: If the
            ``RATELIMIT_PLUS`` setting is malformed.
    """
    return app_settings[key]
