"""Django settings integration for :mod:`drf_n_plus_one_query_guard`.

All configuration lives under a single Django setting,
``N_PLUS_ONE_GUARD``, a dictionary of overrides merged on top of
:data:`DEFAULTS`. Settings are validated and cached lazily on first
access, and the cache is invalidated automatically when Django's
``setting_changed`` signal fires (which makes
``@override_settings(N_PLUS_ONE_GUARD={...})`` work correctly in tests).

Example:
    .. code-block:: python

        # settings.py
        N_PLUS_ONE_GUARD = {
            "THRESHOLD": 3,
            "MODE": "raise",
        }
"""

from __future__ import annotations

import re
from typing import Any, Final

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test.signals import setting_changed
from django.utils.functional import cached_property

USER_SETTINGS_NAME: Final[str] = "N_PLUS_ONE_GUARD"

_VALID_MODES: Final[frozenset[str]] = frozenset({"warn", "raise", "report"})

#: Default values for every recognized setting. See ``docs/settings.md``
#: for the full description of each key.
DEFAULTS: Final[dict[str, Any]] = {
    #: The number of times an identically-shaped query must repeat within
    #: one guarded scope before it is reported as a suspected N+1. ``2``
    #: means "any repeat at all" - the lowest meaningful threshold.
    "THRESHOLD": 2,
    #: What happens when a violation is found: ``"warn"`` logs via the
    #: standard library ``logging`` module (see ``LOGGER_NAME``),
    #: ``"raise"`` raises :class:`~drf_n_plus_one_query_guard.exceptions.NPlusOneDetectedError`,
    #: ``"report"`` does neither - violations are only available by
    #: reading the guard's own ``.violations`` after the fact (used by
    #: :class:`~drf_n_plus_one_query_guard.middleware.NPlusOneGuardMiddleware`,
    #: which reports via a response header instead of failing the request).
    "MODE": "warn",
    #: Name of the ``logging`` logger used in ``"warn"`` mode.
    "LOGGER_NAME": "drf_n_plus_one_query_guard",
    #: A list of regular expression patterns (matched against the
    #: normalized SQL text via ``re.search``); a query matching any
    #: pattern here is never counted toward a violation. Use this for
    #: known, accepted repeated queries (e.g. a fixed-size lookup loop)
    #: rather than lowering ``THRESHOLD`` project-wide.
    "IGNORE_PATTERNS": [],
    #: Response header name used by
    #: :class:`~drf_n_plus_one_query_guard.middleware.NPlusOneGuardMiddleware`
    #: to report violation counts, only ever added when ``settings.DEBUG``
    #: is ``True`` (never in production, regardless of this setting).
    "RESPONSE_HEADER": "X-N-Plus-One-Warnings",
}

#: Settings whose values must be one of a fixed set of Python types.
_TYPE_CHECKS: Final[dict[str, type | tuple[type, ...]]] = {
    "THRESHOLD": int,
    "MODE": str,
    "LOGGER_NAME": str,
    "IGNORE_PATTERNS": (list, tuple),
    "RESPONSE_HEADER": str,
}


class _NPlusOneGuardSettings:
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
        if merged["THRESHOLD"] < 2:
            raise ImproperlyConfigured(
                f"'{USER_SETTINGS_NAME}[\"THRESHOLD\"]' must be at least 2 "
                "(a single query is never a repetition)."
            )
        if merged["MODE"] not in _VALID_MODES:
            raise ImproperlyConfigured(
                f"'{USER_SETTINGS_NAME}[\"MODE\"]' must be one of "
                f"{sorted(_VALID_MODES)}, got {merged['MODE']!r}."
            )
        for pattern in merged["IGNORE_PATTERNS"]:
            if not isinstance(pattern, str):
                raise ImproperlyConfigured(
                    f"'{USER_SETTINGS_NAME}[\"IGNORE_PATTERNS\"]' entries must be strings, "
                    f"got {type(pattern).__name__}."
                )
            try:
                re.compile(pattern)
            except re.error as exc:
                raise ImproperlyConfigured(
                    f"'{USER_SETTINGS_NAME}[\"IGNORE_PATTERNS\"]' contains an invalid "
                    f"regular expression {pattern!r}: {exc}"
                ) from exc
        return merged

    def __getitem__(self, key: str) -> Any:
        if key not in DEFAULTS:
            raise KeyError(f"Invalid setting: {key!r}. Valid keys are: {sorted(DEFAULTS)}.")
        return self._user_settings[key]

    def _on_setting_changed(self, *, sender: Any, setting: str, **kwargs: Any) -> None:
        if setting == USER_SETTINGS_NAME:
            self.__dict__.pop("_user_settings", None)


app_settings = _NPlusOneGuardSettings()


def get_setting(key: str) -> Any:
    """Return the effective value of a single package setting.

    Args:
        key: One of the keys documented in :data:`DEFAULTS`
            (e.g. ``"THRESHOLD"``, ``"MODE"``, ``"IGNORE_PATTERNS"``).

    Returns:
        The user-configured value if present in the ``N_PLUS_ONE_GUARD``
        Django setting, otherwise the default.

    Raises:
        KeyError: If ``key`` is not a recognized setting name.
        django.core.exceptions.ImproperlyConfigured: If the
            ``N_PLUS_ONE_GUARD`` setting is malformed.
    """
    return app_settings[key]
