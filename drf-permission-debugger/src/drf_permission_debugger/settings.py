"""Django settings integration for :mod:`drf_permission_debugger`.

All configuration lives under a single Django setting,
``PERMISSION_DEBUGGER``, a dictionary of overrides merged on top of
:data:`DEFAULTS`. This mirrors the well-established pattern used by
Django REST Framework's own ``api_settings`` object: settings are
validated and cached lazily on first access, and the cache is
invalidated automatically when Django's ``setting_changed`` signal
fires (which makes ``@override_settings(PERMISSION_DEBUGGER={...})``
work correctly in tests).

Example:
    .. code-block:: python

        # settings.py
        PERMISSION_DEBUGGER = {
            "ENABLED": True,
            "RESTRICT_TO_STAFF": True,
            "HEADER_NAME": "X-Permission-Trace",
        }
"""

from __future__ import annotations

from typing import Any, Final

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test.signals import setting_changed
from django.utils.functional import cached_property

USER_SETTINGS_NAME: Final[str] = "PERMISSION_DEBUGGER"

#: Default values for every recognized setting. See ``docs/settings.md``
#: for the full description of each key.
DEFAULTS: Final[dict[str, Any]] = {
    #: Master switch. When ``False`` (default), no trace is ever
    #: attached to a response, regardless of any other setting - tracing
    #: still runs internally (so ``request_permission_trace()`` works
    #: from your own code), but nothing is exposed over HTTP.
    "ENABLED": False,
    #: When ``True`` (default), the trace is only attached to the
    #: response when ``request.user`` is authenticated and
    #: ``is_staff`` - never for anonymous or non-staff users, even if
    #: ``ENABLED`` is ``True``. Set to ``False`` only in an environment
    #: with no real, untrusted users (a local/staging environment with
    #: no production data) - see ``docs/security.md``.
    "RESTRICT_TO_STAFF": True,
    #: The response header the trace is attached to, as a compact,
    #: single-line summary.
    "HEADER_NAME": "X-Permission-Trace",
    #: When ``True``, a denied (403) response also includes the full
    #: trace as structured JSON under ``"permission_trace"`` in the
    #: response body, not just the summary header.
    "INCLUDE_IN_RESPONSE_BODY": False,
}

#: Settings whose values must be one of a fixed set of Python types.
_TYPE_CHECKS: Final[dict[str, type | tuple[type, ...]]] = {
    "ENABLED": bool,
    "RESTRICT_TO_STAFF": bool,
    "HEADER_NAME": str,
    "INCLUDE_IN_RESPONSE_BODY": bool,
}


class _PermissionDebuggerSettings:
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
        if not merged["HEADER_NAME"]:
            raise ImproperlyConfigured(f"'{USER_SETTINGS_NAME}[\"HEADER_NAME\"]' cannot be empty.")
        return merged

    def __getitem__(self, key: str) -> Any:
        if key not in DEFAULTS:
            raise KeyError(f"Invalid setting: {key!r}. Valid keys are: {sorted(DEFAULTS)}.")
        return self._user_settings[key]

    def _on_setting_changed(self, *, sender: Any, setting: str, **kwargs: Any) -> None:
        if setting == USER_SETTINGS_NAME:
            self.__dict__.pop("_user_settings", None)


app_settings = _PermissionDebuggerSettings()


def get_setting(key: str) -> Any:
    """Return the effective value of a single package setting.

    Args:
        key: One of the keys documented in :data:`DEFAULTS`
            (e.g. ``"ENABLED"``, ``"RESTRICT_TO_STAFF"``).

    Returns:
        The user-configured value if present in the
        ``PERMISSION_DEBUGGER`` Django setting, otherwise the default.

    Raises:
        KeyError: If ``key`` is not a recognized setting name.
        django.core.exceptions.ImproperlyConfigured: If the
            ``PERMISSION_DEBUGGER`` setting is malformed.
    """
    return app_settings[key]
