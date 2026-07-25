"""Django settings integration for :mod:`drf_serializer_performance_profiler`.

All configuration lives under a single Django setting,
``SERIALIZER_PROFILER``, a dictionary of overrides merged on top of
:data:`DEFAULTS`. This mirrors the well-established pattern used by
Django REST Framework's own ``api_settings`` object: settings are
validated and cached lazily on first access, and the cache is
invalidated automatically when Django's ``setting_changed`` signal
fires (which makes ``@override_settings(SERIALIZER_PROFILER={...})``
work correctly in tests).

Example:
    .. code-block:: python

        # settings.py
        SERIALIZER_PROFILER = {
            "ENABLED": True,
            "LOG_SLOW_FIELDS": True,
            "SLOW_FIELD_THRESHOLD_MS": 10.0,
        }
"""

from __future__ import annotations

from typing import Any, Final

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test.signals import setting_changed
from django.utils.functional import cached_property

USER_SETTINGS_NAME: Final[str] = "SERIALIZER_PROFILER"

#: Default values for every recognized setting. See ``docs/settings.md``
#: for the full description of each key.
DEFAULTS: Final[dict[str, Any]] = {
    #: Master switch for the ``X-Serializer-Profile`` response header.
    #: When ``False`` (default), no header is ever attached, regardless
    #: of any other setting - per-field instrumentation still runs
    #: whenever this OR ``LOG_SLOW_FIELDS`` is ``True``, so
    #: ``get_serializer_profile()`` works from your own code either way.
    "ENABLED": False,
    #: When ``True`` (default), the header is only attached when
    #: ``request.user`` is authenticated and ``is_staff`` - never for
    #: anonymous or non-staff users, even if ``ENABLED`` is ``True``.
    #: See ``docs/security.md``.
    "RESTRICT_TO_STAFF": True,
    #: The response header the compact profile summary is attached to.
    "HEADER_NAME": "X-Serializer-Profile",
    #: When ``True``, any field whose total time for a given request
    #: meets or exceeds ``SLOW_FIELD_THRESHOLD_MS`` is logged via
    #: Python's ``logging`` module (logger name
    #: ``"drf_serializer_performance_profiler"``) - independent of
    #: ``ENABLED``/``RESTRICT_TO_STAFF``, since this never exposes
    #: anything over HTTP. Safe to enable in production for ongoing
    #: monitoring.
    "LOG_SLOW_FIELDS": False,
    #: The threshold (in milliseconds) a field's total time must meet
    #: or exceed to be logged when ``LOG_SLOW_FIELDS`` is ``True``.
    "SLOW_FIELD_THRESHOLD_MS": 5.0,
}

#: Settings whose values must be one of a fixed set of Python types.
_TYPE_CHECKS: Final[dict[str, type | tuple[type, ...]]] = {
    "ENABLED": bool,
    "RESTRICT_TO_STAFF": bool,
    "HEADER_NAME": str,
    "LOG_SLOW_FIELDS": bool,
    "SLOW_FIELD_THRESHOLD_MS": (int, float),
}


class _SerializerProfilerSettings:
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
            value = merged[key]
            # bool is a subclass of int, so isinstance(True, (int, float))
            # is True - explicitly reject it for the numeric setting, since
            # a threshold of `True`/`False` is never meaningful.
            is_bool_where_numeric_expected = isinstance(value, bool) and expected_type is not bool
            if is_bool_where_numeric_expected or not isinstance(value, expected_type):
                raise ImproperlyConfigured(
                    f"'{USER_SETTINGS_NAME}[\"{key}\"]' must be of type "
                    f"{expected_type}, got {type(value).__name__}."
                )
        if not merged["HEADER_NAME"]:
            raise ImproperlyConfigured(f"'{USER_SETTINGS_NAME}[\"HEADER_NAME\"]' cannot be empty.")
        if merged["SLOW_FIELD_THRESHOLD_MS"] < 0:
            raise ImproperlyConfigured(
                f"'{USER_SETTINGS_NAME}[\"SLOW_FIELD_THRESHOLD_MS\"]' cannot be negative."
            )
        return merged

    def __getitem__(self, key: str) -> Any:
        if key not in DEFAULTS:
            raise KeyError(f"Invalid setting: {key!r}. Valid keys are: {sorted(DEFAULTS)}.")
        return self._user_settings[key]

    def _on_setting_changed(self, *, sender: Any, setting: str, **kwargs: Any) -> None:
        if setting == USER_SETTINGS_NAME:
            self.__dict__.pop("_user_settings", None)


app_settings = _SerializerProfilerSettings()


def get_setting(key: str) -> Any:
    """Return the effective value of a single package setting.

    Args:
        key: One of the keys documented in :data:`DEFAULTS`
            (e.g. ``"ENABLED"``, ``"SLOW_FIELD_THRESHOLD_MS"``).

    Returns:
        The user-configured value if present in the
        ``SERIALIZER_PROFILER`` Django setting, otherwise the default.

    Raises:
        KeyError: If ``key`` is not a recognized setting name.
        django.core.exceptions.ImproperlyConfigured: If the
            ``SERIALIZER_PROFILER`` setting is malformed.
    """
    return app_settings[key]
