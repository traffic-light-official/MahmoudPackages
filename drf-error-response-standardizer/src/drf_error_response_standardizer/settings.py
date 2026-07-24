"""Django settings integration for :mod:`drf_error_response_standardizer`.

All configuration lives under a single Django setting,
``ERROR_RESPONSE_STANDARDIZER``, a dictionary of overrides merged on top of
:data:`DEFAULTS`. This mirrors the pattern used by Django REST Framework's
own ``api_settings`` object: settings are validated and cached lazily on
first access, and the cache is invalidated automatically when Django's
``setting_changed`` signal fires (which makes
``@override_settings(ERROR_RESPONSE_STANDARDIZER={...})`` work correctly in
tests).

Example:
    .. code-block:: python

        # settings.py
        ERROR_RESPONSE_STANDARDIZER = {
            "TYPE_BASE_URI": "https://api.example.com/problems/",
            "INCLUDE_TRACE_ID": True,
        }
"""

from __future__ import annotations

from typing import Any, Final

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test.signals import setting_changed
from django.utils.functional import cached_property

USER_SETTINGS_NAME: Final[str] = "ERROR_RESPONSE_STANDARDIZER"

#: Default values for every recognized setting. See ``docs/settings.md`` for
#: the full description of each key.
DEFAULTS: Final[dict[str, Any]] = {
    #: Base URI prepended to relative problem type slugs registered via
    #: :func:`~drf_error_response_standardizer.registry.register`, e.g.
    #: ``"https://api.example.com/problems/"`` + ``"out-of-stock"`` ->
    #: ``"https://api.example.com/problems/out-of-stock"``. When ``None``,
    #: the raw ``about:blank`` URI (or the exception's own absolute type
    #: URI, if it supplied one) is used unchanged.
    "TYPE_BASE_URI": None,
    #: Value written to the ``Content-Type`` header of error responses.
    #: Set to ``"application/json"`` if a legacy frontend cannot yet parse
    #: ``application/problem+json`` and strict content negotiation would
    #: break it. Set to ``None`` to leave DRF's default negotiated content
    #: type untouched.
    "MEDIA_TYPE": "application/problem+json",
    #: When ``True`` (default), the ``instance`` member is set to the
    #: request's path (``request.path``), per RFC 9457 section 3.1.4.
    "INCLUDE_INSTANCE": True,
    #: When ``True``, a ``correlation_id`` extension member is included,
    #: sourced from :class:`~drf_error_response_standardizer.middleware.CorrelationIdMiddleware`.
    "INCLUDE_CORRELATION_ID": True,
    #: When ``True``, a ``request_id`` extension member is included.
    "INCLUDE_REQUEST_ID": True,
    #: When ``True``, a ``trace_id`` extension member is included whenever
    #: a W3C ``traceparent`` header was present on the request.
    "INCLUDE_TRACE_ID": True,
    #: When ``True``, a ``timestamp`` extension member (ISO 8601, UTC) is
    #: included, recording when the problem response was generated.
    "INCLUDE_TIMESTAMP": True,
    #: When ``True`` (default), validation errors from
    #: :class:`rest_framework.exceptions.ValidationError` are expanded into
    #: an ``errors`` extension array of ``{"pointer", "detail", "code"}``
    #: objects, one per invalid field (including nested serializers).
    "EXPAND_VALIDATION_ERRORS": True,
    #: Dotted path to a callable used to build the ``detail`` message for
    #: uncaught, non-API exceptions (500s). Defaults to a generic,
    #: non-leaky message. Override to customize wording; never make this
    #: return exception internals in production.
    "SERVER_ERROR_DETAIL": "A server error occurred. Please try again later.",
    #: When ``True``, unhandled exceptions that are not
    #: :class:`~rest_framework.exceptions.APIException` subclasses (e.g. a
    #: raw ``ValueError`` bubbling out of a view) are also converted into a
    #: 500 Problem Details response instead of propagating to Django's
    #: default error handling. Set to ``False`` to let Django's own
    #: ``DEBUG``-aware error pages/signals handle those instead.
    "CATCH_ALL_EXCEPTIONS": True,
    #: When ``True``, enables the ``drf-standardized-errors``-compatible
    #: response shape (``{"type", "errors": [{"code", "detail", "attr"}]}``)
    #: in addition to the RFC 9457 members, for projects migrating from
    #: that package. See ``docs/faq.md``.
    "STANDARDIZED_ERRORS_COMPAT": False,
}

#: Settings whose values must be one of a fixed set of Python types.
_TYPE_CHECKS: Final[dict[str, type | tuple[type, ...]]] = {
    "TYPE_BASE_URI": (str, type(None)),
    "MEDIA_TYPE": (str, type(None)),
    "INCLUDE_INSTANCE": bool,
    "INCLUDE_CORRELATION_ID": bool,
    "INCLUDE_REQUEST_ID": bool,
    "INCLUDE_TRACE_ID": bool,
    "INCLUDE_TIMESTAMP": bool,
    "EXPAND_VALIDATION_ERRORS": bool,
    "SERVER_ERROR_DETAIL": str,
    "CATCH_ALL_EXCEPTIONS": bool,
    "STANDARDIZED_ERRORS_COMPAT": bool,
}


class _ErrorResponseStandardizerSettings:
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
        if merged["TYPE_BASE_URI"] is not None and not merged["TYPE_BASE_URI"].endswith("/"):
            raise ImproperlyConfigured(
                f"'{USER_SETTINGS_NAME}[\"TYPE_BASE_URI\"]' must end with '/', "
                f"got {merged['TYPE_BASE_URI']!r}."
            )
        return merged

    def __getitem__(self, key: str) -> Any:
        if key not in DEFAULTS:
            raise KeyError(f"Invalid setting: {key!r}. Valid keys are: {sorted(DEFAULTS)}.")
        return self._user_settings[key]

    def _on_setting_changed(self, *, sender: Any, setting: str, **kwargs: Any) -> None:
        if setting == USER_SETTINGS_NAME:
            self.__dict__.pop("_user_settings", None)


app_settings = _ErrorResponseStandardizerSettings()


def get_setting(key: str) -> Any:
    """Return the effective value of a single package setting.

    Args:
        key: One of the keys documented in :data:`DEFAULTS` (e.g.
            ``"TYPE_BASE_URI"``, ``"MEDIA_TYPE"``, ``"INCLUDE_TRACE_ID"``).

    Returns:
        The user-configured value if present in the
        ``ERROR_RESPONSE_STANDARDIZER`` Django setting, otherwise the
        default.

    Raises:
        KeyError: If ``key`` is not a recognized setting name.
        django.core.exceptions.ImproperlyConfigured: If the
            ``ERROR_RESPONSE_STANDARDIZER`` setting is malformed.
    """
    return app_settings[key]
