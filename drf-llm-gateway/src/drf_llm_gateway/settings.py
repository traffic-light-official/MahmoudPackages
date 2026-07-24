"""Django settings integration for :mod:`drf_llm_gateway`.

All configuration lives under a single Django setting, ``LLM_GATEWAY``, a
dictionary of overrides merged on top of :data:`DEFAULTS`. See
``docs/settings.md`` for the description of every key.
"""

from __future__ import annotations

from typing import Any, Final

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test.signals import setting_changed
from django.utils.functional import cached_property

USER_SETTINGS_NAME: Final[str] = "LLM_GATEWAY"

DEFAULTS: Final[dict[str, Any]] = {
    #: Separator used to build default tool names from a viewset's base
    #: name and action, e.g. ``"article" + "_" + "list"`` -> ``"article_list"``.
    "NAME_SEPARATOR": "_",
    #: Maximum number of enum values inlined into a ``ChoiceField``'s JSON
    #: Schema ``enum`` list. Choice fields with more options than this
    #: fall back to a plain ``"type": "string"`` schema (with a note in
    #: the description) to avoid enormous generated schemas.
    "MAX_ENUM_VALUES": 100,
    #: Maximum recursion depth when converting nested serializers to JSON
    #: Schema. Protects against accidental self-referential serializers.
    "MAX_SCHEMA_DEPTH": 8,
    #: When ``True``, examples attached via ``@expose_as_tool(examples=...)``
    #: are embedded in the generated JSON Schema under an ``"examples"``
    #: key. When ``False``, examples are still available on the
    #: ``ToolDefinition`` object but omitted from the generated schema.
    "INCLUDE_EXAMPLES_IN_SCHEMA": True,
    #: When ``True`` (default), :func:`~drf_llm_gateway.executor.execute_tool`
    #: enforces each tool's ``permission_classes`` against the calling
    #: request/user before dispatching. Disable only for trusted, internal
    #: execution contexts that perform their own authorization.
    "ENFORCE_PERMISSIONS": True,
}

_TYPE_CHECKS: Final[dict[str, type | tuple[type, ...]]] = {
    "NAME_SEPARATOR": str,
    "MAX_ENUM_VALUES": int,
    "MAX_SCHEMA_DEPTH": int,
    "INCLUDE_EXAMPLES_IN_SCHEMA": bool,
    "ENFORCE_PERMISSIONS": bool,
}


class _LLMGatewaySettings:
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
        if merged["MAX_ENUM_VALUES"] < 1:
            raise ImproperlyConfigured(f"'{USER_SETTINGS_NAME}[\"MAX_ENUM_VALUES\"]' must be >= 1.")
        if merged["MAX_SCHEMA_DEPTH"] < 1:
            raise ImproperlyConfigured(
                f"'{USER_SETTINGS_NAME}[\"MAX_SCHEMA_DEPTH\"]' must be >= 1."
            )
        if not merged["NAME_SEPARATOR"]:
            raise ImproperlyConfigured(
                f"'{USER_SETTINGS_NAME}[\"NAME_SEPARATOR\"]' must be a non-empty string."
            )
        return merged

    def __getitem__(self, key: str) -> Any:
        if key not in DEFAULTS:
            raise KeyError(f"Invalid setting: {key!r}. Valid keys are: {sorted(DEFAULTS)}.")
        return self._user_settings[key]

    def _on_setting_changed(self, *, sender: Any, setting: str, **kwargs: Any) -> None:
        if setting == USER_SETTINGS_NAME:
            self.__dict__.pop("_user_settings", None)


app_settings = _LLMGatewaySettings()


def get_setting(key: str) -> Any:
    """Return the effective value of a single package setting.

    Args:
        key: One of the keys documented in :data:`DEFAULTS`.

    Returns:
        The user-configured value if present in the ``LLM_GATEWAY`` Django
        setting, otherwise the default.

    Raises:
        KeyError: If ``key`` is not a recognized setting name.
        django.core.exceptions.ImproperlyConfigured: If the ``LLM_GATEWAY``
            setting is malformed.
    """
    return app_settings[key]
