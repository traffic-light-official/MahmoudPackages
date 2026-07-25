"""Django settings integration for :mod:`drf_bulk_operations`.

All configuration lives under a single Django setting,
``BULK_OPERATIONS``, a dictionary of overrides merged on top of
:data:`DEFAULTS`. This mirrors the well-established pattern used by
Django REST Framework's own ``api_settings`` object: settings are
validated and cached lazily on first access, and the cache is
invalidated automatically when Django's ``setting_changed`` signal
fires (which makes ``@override_settings(BULK_OPERATIONS={...})`` work
correctly in tests).

Example:
    .. code-block:: python

        # settings.py
        BULK_OPERATIONS = {
            "MAX_BATCH_SIZE": 500,
            "ATOMIC": False,
        }
"""

from __future__ import annotations

from typing import Any, Final

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test.signals import setting_changed
from django.utils.functional import cached_property

USER_SETTINGS_NAME: Final[str] = "BULK_OPERATIONS"

#: Default values for every recognized setting. See ``docs/settings.md``
#: for the full description of each key.
DEFAULTS: Final[dict[str, Any]] = {
    #: Maximum number of items accepted in a single bulk request. Protects
    #: against a client submitting an unbounded payload that would hold a
    #: database transaction (or a long loop of independent saves) open for
    #: an excessive amount of time.
    "MAX_BATCH_SIZE": 100,
    #: When ``True`` (default), an entire bulk request is wrapped in one
    #: database transaction: if any item fails validation or fails to
    #: save, nothing is committed and a single 400 response lists every
    #: item's errors by index. When ``False``, each item is attempted
    #: independently (in its own savepoint) and the response reports
    #: per-item success/failure, so some items can succeed even if others
    #: fail. See ``docs/architecture.md``.
    "ATOMIC": True,
}

#: Settings whose values must be one of a fixed set of Python types.
_TYPE_CHECKS: Final[dict[str, type | tuple[type, ...]]] = {
    "MAX_BATCH_SIZE": int,
    "ATOMIC": bool,
}


class _BulkOperationsSettings:
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
        if merged["MAX_BATCH_SIZE"] < 1:
            raise ImproperlyConfigured(
                f"'{USER_SETTINGS_NAME}[\"MAX_BATCH_SIZE\"]' must be at least 1."
            )
        return merged

    def __getitem__(self, key: str) -> Any:
        if key not in DEFAULTS:
            raise KeyError(f"Invalid setting: {key!r}. Valid keys are: {sorted(DEFAULTS)}.")
        return self._user_settings[key]

    def _on_setting_changed(self, *, sender: Any, setting: str, **kwargs: Any) -> None:
        if setting == USER_SETTINGS_NAME:
            self.__dict__.pop("_user_settings", None)


app_settings = _BulkOperationsSettings()


def get_setting(key: str) -> Any:
    """Return the effective value of a single package setting.

    Args:
        key: One of the keys documented in :data:`DEFAULTS`
            (e.g. ``"MAX_BATCH_SIZE"``, ``"ATOMIC"``).

    Returns:
        The user-configured value if present in the ``BULK_OPERATIONS``
        Django setting, otherwise the default.

    Raises:
        KeyError: If ``key`` is not a recognized setting name.
        django.core.exceptions.ImproperlyConfigured: If the
            ``BULK_OPERATIONS`` setting is malformed.
    """
    return app_settings[key]
