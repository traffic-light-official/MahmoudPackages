"""Django settings integration for :mod:`drf_partial_response_fields`.

All configuration lives under a single Django setting,
``PARTIAL_RESPONSE_FIELDS``, a dictionary of overrides merged on top of
:data:`DEFAULTS`. This mirrors the well-established pattern used by Django
REST Framework's own ``api_settings`` object: settings are validated and
cached lazily on first access, and the cache is invalidated automatically
when Django's ``setting_changed`` signal fires (which makes
``@override_settings(PARTIAL_RESPONSE_FIELDS={...})`` work correctly in
tests).

Example:
    .. code-block:: python

        # settings.py
        PARTIAL_RESPONSE_FIELDS = {
            "QUERY_PARAM": "fields",
            "STRICT": True,
            "MAX_DEPTH": 4,
        }
"""

from __future__ import annotations

from typing import Any, Final

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test.signals import setting_changed
from django.utils.functional import cached_property

USER_SETTINGS_NAME: Final[str] = "PARTIAL_RESPONSE_FIELDS"

#: Default values for every recognized setting. See ``docs/settings.md``
#: for the full description of each key.
DEFAULTS: Final[dict[str, Any]] = {
    #: Name of the query parameter clients use to request a subset of
    #: fields, e.g. ``?fields=id,name``.
    "QUERY_PARAM": "fields",
    #: Maximum allowed nesting depth of the ``fields`` expression, e.g.
    #: ``a(b(c(d)))`` has depth 4. Protects against pathological input.
    "MAX_DEPTH": 6,
    #: Maximum accepted length (in characters) of the raw ``fields`` query
    #: parameter. Requests exceeding this are rejected before parsing.
    "MAX_FIELDS_LENGTH": 2000,
    #: When ``True``, requesting a field name that does not exist on the
    #: serializer raises :class:`~drf_partial_response_fields.exceptions.UnknownFieldError`
    #: (HTTP 400). When ``False`` (default), unknown names are silently
    #: dropped, matching the permissive behavior of most sparse-fieldset
    #: implementations.
    "STRICT": False,
    #: Field names that are always included in the response regardless of
    #: the ``fields`` parameter. The primary key is included by default
    #: because pagination, hyperlinking, and client-side caching typically
    #: depend on it being present.
    "ALWAYS_INCLUDE": ["id"],
    #: When ``False``, disables the automatic ``select_related`` /
    #: ``prefetch_related`` / ``only`` optimization performed by
    #: :class:`~drf_partial_response_fields.mixins.PartialResponseMixin`.
    #: The fields filtering itself is unaffected; only the queryset
    #: optimization step is skipped.
    "ENABLE_QUERY_OPTIMIZATION": True,
    #: When ``True`` (default), :class:`~drf_partial_response_fields.mixins.PartialResponseMixin`
    #: only honors the ``fields`` parameter on safe HTTP methods (``GET``,
    #: ``HEAD``, ``OPTIONS``); unsafe methods (``POST``, ``PUT``, ``PATCH``,
    #: ``DELETE``) always see the full, unfiltered field set. This matters
    #: because DRF serializers use the same field set for both input
    #: validation and output rendering: without this guard, a client could
    #: use ``?fields=`` to make required writable fields disappear from
    #: input validation entirely. Set to ``False`` only if you have verified
    #: your write endpoints do not rely on fields being present that a
    #: client might omit via ``fields=``.
    "SAFE_METHODS_ONLY": True,
}

#: Settings whose values must be one of a fixed set of Python types.
_TYPE_CHECKS: Final[dict[str, type | tuple[type, ...]]] = {
    "QUERY_PARAM": str,
    "MAX_DEPTH": int,
    "MAX_FIELDS_LENGTH": int,
    "STRICT": bool,
    "ALWAYS_INCLUDE": (list, tuple),
    "ENABLE_QUERY_OPTIMIZATION": bool,
    "SAFE_METHODS_ONLY": bool,
}


class _PartialResponseFieldsSettings:
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
        if merged["MAX_DEPTH"] < 1:
            raise ImproperlyConfigured(f"'{USER_SETTINGS_NAME}[\"MAX_DEPTH\"]' must be at least 1.")
        if merged["MAX_FIELDS_LENGTH"] < 1:
            raise ImproperlyConfigured(
                f"'{USER_SETTINGS_NAME}[\"MAX_FIELDS_LENGTH\"]' must be at least 1."
            )
        if not merged["QUERY_PARAM"].isidentifier():
            raise ImproperlyConfigured(
                f"'{USER_SETTINGS_NAME}[\"QUERY_PARAM\"]' must be a valid identifier, "
                f"got {merged['QUERY_PARAM']!r}."
            )
        return merged

    def __getitem__(self, key: str) -> Any:
        if key not in DEFAULTS:
            raise KeyError(f"Invalid setting: {key!r}. Valid keys are: {sorted(DEFAULTS)}.")
        return self._user_settings[key]

    def _on_setting_changed(self, *, sender: Any, setting: str, **kwargs: Any) -> None:
        if setting == USER_SETTINGS_NAME:
            self.__dict__.pop("_user_settings", None)


app_settings = _PartialResponseFieldsSettings()


def get_setting(key: str) -> Any:
    """Return the effective value of a single package setting.

    Args:
        key: One of the keys documented in :data:`DEFAULTS`
            (e.g. ``"QUERY_PARAM"``, ``"STRICT"``, ``"MAX_DEPTH"``).

    Returns:
        The user-configured value if present in the
        ``PARTIAL_RESPONSE_FIELDS`` Django setting, otherwise the default.

    Raises:
        KeyError: If ``key`` is not a recognized setting name.
        django.core.exceptions.ImproperlyConfigured: If the
            ``PARTIAL_RESPONSE_FIELDS`` setting is malformed.
    """
    return app_settings[key]
