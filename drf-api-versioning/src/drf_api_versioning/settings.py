"""Django settings integration for :mod:`drf_api_versioning`.

All configuration lives under a single Django setting, ``API_VERSIONING``,
validated and cached lazily on first access; the cache is invalidated
automatically when Django's ``setting_changed`` signal fires (which
makes ``@override_settings(API_VERSIONING={...})`` work correctly in
tests).

Example:
    .. code-block:: python

        # settings.py
        import datetime

        API_VERSIONING = {
            "VERSIONS": {
                "v1": {
                    "deprecated": datetime.date(2026, 1, 1),
                    "sunset": datetime.date(2026, 7, 1),
                    "deprecation_link": "https://example.com/docs/migrating-to-v2",
                },
                "v2": {},
            },
            "DEFAULT_VERSION": "v2",
        }
"""

from __future__ import annotations

import datetime
from typing import Any, Final

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test.signals import setting_changed
from django.utils.functional import cached_property

USER_SETTINGS_NAME: Final[str] = "API_VERSIONING"

#: Default values for every recognized setting. See ``docs/settings.md``
#: for the full description of each key.
DEFAULTS: Final[dict[str, Any]] = {
    #: A mapping of version name to its metadata dict. Each entry may
    #: have ``"deprecated"`` and/or ``"sunset"`` (``datetime.date`` or
    #: ``datetime.datetime``) and ``"deprecation_link"`` (a URL string),
    #: all optional. A version present as a bare key with an empty dict
    #: (or omitted keys) is considered fully supported, not deprecated.
    "VERSIONS": {},
    #: The version used when a request does not specify one (passed
    #: through to DRF's own ``BaseVersioning.default_version``). Must be
    #: a key in ``VERSIONS``, or ``None`` to require every request to
    #: specify a version explicitly.
    "DEFAULT_VERSION": None,
    #: When ``False`` (default), a request resolving to a version past
    #: its ``sunset`` date is rejected with
    #: :class:`~drf_api_versioning.exceptions.APIVersionSunsetError`
    #: (HTTP 410). When ``True``, sunset versions are still served
    #: normally (headers are still added) - useful for a soft rollout of
    #: sunset dates before actually enforcing them.
    "ALLOW_SUNSET": False,
    #: Response header name used to signal deprecation (see
    #: ``docs/architecture.md`` for the exact format).
    "DEPRECATION_HEADER": "Deprecation",
    #: Response header name used to signal the sunset date (RFC 8594).
    "SUNSET_HEADER": "Sunset",
    #: Response header name used for the migration-docs ``Link``, when a
    #: version defines ``deprecation_link``.
    "LINK_HEADER": "Link",
}

#: Settings whose values must be one of a fixed set of Python types.
_TYPE_CHECKS: Final[dict[str, type | tuple[type, ...]]] = {
    "VERSIONS": dict,
    "ALLOW_SUNSET": bool,
    "DEPRECATION_HEADER": str,
    "SUNSET_HEADER": str,
    "LINK_HEADER": str,
}


class _ApiVersioningSettings:
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
        _validate_versions(merged["VERSIONS"])
        _validate_default_version(merged["DEFAULT_VERSION"], merged["VERSIONS"])
        return merged

    def __getitem__(self, key: str) -> Any:
        if key not in DEFAULTS:
            raise KeyError(f"Invalid setting: {key!r}. Valid keys are: {sorted(DEFAULTS)}.")
        return self._user_settings[key]

    def _on_setting_changed(self, *, sender: Any, setting: str, **kwargs: Any) -> None:
        if setting == USER_SETTINGS_NAME:
            self.__dict__.pop("_user_settings", None)


def _validate_versions(versions: dict[str, Any]) -> None:
    if not versions:
        raise ImproperlyConfigured(
            f"'{USER_SETTINGS_NAME}[\"VERSIONS\"]' must declare at least one version."
        )
    for name, entry in versions.items():
        if not isinstance(name, str) or not name:
            raise ImproperlyConfigured(
                f"'{USER_SETTINGS_NAME}[\"VERSIONS\"]' keys must be non-empty strings, "
                f"got {name!r}."
            )
        if not isinstance(entry, dict):
            raise ImproperlyConfigured(
                f'\'{USER_SETTINGS_NAME}["VERSIONS"]["{name}"]\' must be a dict, '
                f"got {type(entry).__name__}."
            )
        unknown_keys = set(entry) - {"deprecated", "sunset", "deprecation_link"}
        if unknown_keys:
            raise ImproperlyConfigured(
                f'Unknown key(s) in \'{USER_SETTINGS_NAME}["VERSIONS"]["{name}"]\': '
                f"{sorted(unknown_keys)}."
            )
        for date_key in ("deprecated", "sunset"):
            value = entry.get(date_key)
            if value is not None and not isinstance(value, datetime.date):
                raise ImproperlyConfigured(
                    f'\'{USER_SETTINGS_NAME}["VERSIONS"]["{name}"]["{date_key}"]\' must be '
                    f"a datetime.date, got {type(value).__name__}."
                )
        link = entry.get("deprecation_link")
        if link is not None and not isinstance(link, str):
            raise ImproperlyConfigured(
                f'\'{USER_SETTINGS_NAME}["VERSIONS"]["{name}"]["deprecation_link"]\' must be '
                f"a str, got {type(link).__name__}."
            )
        deprecated, sunset = entry.get("deprecated"), entry.get("sunset")
        if deprecated is not None and sunset is not None and sunset < deprecated:
            raise ImproperlyConfigured(
                f'\'{USER_SETTINGS_NAME}["VERSIONS"]["{name}"]\': "sunset" cannot be '
                'earlier than "deprecated".'
            )


def _validate_default_version(default_version: str | None, versions: dict[str, Any]) -> None:
    if default_version is not None and default_version not in versions:
        raise ImproperlyConfigured(
            f"'{USER_SETTINGS_NAME}[\"DEFAULT_VERSION\"]' ({default_version!r}) must be a key "
            f"in '{USER_SETTINGS_NAME}[\"VERSIONS\"]' ({sorted(versions)}), or None."
        )


app_settings = _ApiVersioningSettings()


def get_setting(key: str) -> Any:
    """Return the effective value of a single package setting.

    Args:
        key: One of the keys documented in :data:`DEFAULTS`
            (e.g. ``"VERSIONS"``, ``"DEFAULT_VERSION"``, ``"ALLOW_SUNSET"``).

    Returns:
        The user-configured value if present in the ``API_VERSIONING``
        Django setting, otherwise the default.

    Raises:
        KeyError: If ``key`` is not a recognized setting name.
        django.core.exceptions.ImproperlyConfigured: If the
            ``API_VERSIONING`` setting is malformed.
    """
    return app_settings[key]
