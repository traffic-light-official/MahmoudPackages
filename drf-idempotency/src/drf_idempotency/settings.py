"""Django settings integration for :mod:`drf_idempotency`.

All configuration lives under a single Django setting, ``IDEMPOTENCY``, a
dictionary of overrides merged on top of :data:`DEFAULTS`. See
``docs/settings.md`` for the description of every key.
"""

from __future__ import annotations

from typing import Any, Final

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test.signals import setting_changed
from django.utils.functional import cached_property

USER_SETTINGS_NAME: Final[str] = "IDEMPOTENCY"

DEFAULTS: Final[dict[str, Any]] = {
    #: The HTTP request header carrying the client-supplied idempotency key.
    "HEADER_NAME": "Idempotency-Key",
    #: The HTTP response header set to ``"true"`` on a replayed (cached)
    #: response, and ``"false"`` on a freshly-executed one.
    "REPLAY_HEADER_NAME": "Idempotent-Replayed",
    #: HTTP methods this package applies to. Requests using any other
    #: method are passed through untouched.
    "METHODS": ["POST", "PUT", "PATCH"],
    #: Dotted path to the backend class used to store idempotency records.
    "BACKEND": "drf_idempotency.backends.database.DatabaseBackend",
    #: Extra keyword arguments passed to the backend's constructor.
    "BACKEND_OPTIONS": {},
    #: How long a completed response is retained and eligible for replay.
    "TTL_SECONDS": 86400,
    #: How long an in-progress lock is held before it is considered
    #: abandoned (e.g. the process handling the original request crashed)
    #: and a new attempt is allowed to proceed.
    "LOCK_TTL_SECONDS": 30,
    #: When ``True``, requests using a method in ``METHODS`` without the
    #: idempotency header are rejected with ``400 Bad Request``. When
    #: ``False`` (default), such requests are processed normally, without
    #: any idempotency handling.
    "REQUIRE_KEY": False,
    #: Maximum accepted length of the idempotency key itself.
    "MAX_KEY_LENGTH": 255,
    #: Whether ``4xx`` responses are cached and replayed like successful
    #: ones (matching Stripe's behavior: a validation error is
    #: deterministic for a given request body, so it's safe to replay).
    #: ``5xx`` responses are never cached regardless of this setting,
    #: since they typically represent a transient failure worth retrying
    #: for real.
    "CACHE_CLIENT_ERROR_RESPONSES": True,
}

_TYPE_CHECKS: Final[dict[str, type | tuple[type, ...]]] = {
    "HEADER_NAME": str,
    "REPLAY_HEADER_NAME": str,
    "METHODS": (list, tuple),
    "BACKEND": str,
    "BACKEND_OPTIONS": dict,
    "TTL_SECONDS": int,
    "LOCK_TTL_SECONDS": int,
    "REQUIRE_KEY": bool,
    "MAX_KEY_LENGTH": int,
    "CACHE_CLIENT_ERROR_RESPONSES": bool,
}


class _IdempotencySettings:
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
        if merged["TTL_SECONDS"] < 1:
            raise ImproperlyConfigured(f"'{USER_SETTINGS_NAME}[\"TTL_SECONDS\"]' must be >= 1.")
        if merged["LOCK_TTL_SECONDS"] < 1:
            raise ImproperlyConfigured(
                f"'{USER_SETTINGS_NAME}[\"LOCK_TTL_SECONDS\"]' must be >= 1."
            )
        if merged["MAX_KEY_LENGTH"] < 1:
            raise ImproperlyConfigured(f"'{USER_SETTINGS_NAME}[\"MAX_KEY_LENGTH\"]' must be >= 1.")
        merged["METHODS"] = {str(m).upper() for m in merged["METHODS"]}
        return merged

    def __getitem__(self, key: str) -> Any:
        if key not in DEFAULTS:
            raise KeyError(f"Invalid setting: {key!r}. Valid keys are: {sorted(DEFAULTS)}.")
        return self._user_settings[key]

    def _on_setting_changed(self, *, sender: Any, setting: str, **kwargs: Any) -> None:
        if setting == USER_SETTINGS_NAME:
            self.__dict__.pop("_user_settings", None)


app_settings = _IdempotencySettings()


def get_setting(key: str) -> Any:
    """Return the effective value of a single package setting.

    Args:
        key: One of the keys documented in :data:`DEFAULTS`.

    Returns:
        The user-configured value if present in the ``IDEMPOTENCY``
        Django setting, otherwise the default.

    Raises:
        KeyError: If ``key`` is not a recognized setting name.
        django.core.exceptions.ImproperlyConfigured: If the
            ``IDEMPOTENCY`` setting is malformed.
    """
    return app_settings[key]
