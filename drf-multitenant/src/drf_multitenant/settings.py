"""Django settings integration for :mod:`drf_multitenant`.

All configuration lives under a single Django setting, ``MULTITENANT``, a
dictionary of overrides merged on top of :data:`DEFAULTS`. See
``docs/settings.md`` for the description of every key.
"""

from __future__ import annotations

from typing import Any, Final

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test.signals import setting_changed
from django.utils.functional import cached_property

USER_SETTINGS_NAME: Final[str] = "MULTITENANT"

DEFAULTS: Final[dict[str, Any]] = {
    #: ``"app_label.ModelName"`` identifying your tenant model. Required
    #: by the built-in ``header_resolver``/``subdomain_resolver`` (which
    #: need to look up a tenant instance); not needed if you only use
    #: ``user_attr_resolver`` or a custom resolver that doesn't query it.
    "TENANT_MODEL": None,
    #: Name of the field (on every tenant-scoped model) holding the
    #: tenant foreign key. Override if your schema uses a different
    #: name (e.g. ``"organization"``, ``"account"``).
    "TENANT_FIELD": "tenant",
    #: Dotted path to a callable ``(request) -> tenant | None`` used by
    #: :class:`~drf_multitenant.middleware.TenantMiddleware` to resolve
    #: the current tenant from an incoming request.
    "RESOLVER": "drf_multitenant.resolvers.header_resolver",
    #: Header name read by the built-in ``header_resolver``.
    "TENANT_HEADER": "X-Tenant-ID",
    #: Attribute name read off ``request.user`` by the built-in
    #: ``user_attr_resolver``.
    "USER_TENANT_ATTR": "tenant",
    #: If ``True`` (default), ``TenantMiddleware`` rejects any request
    #: for which no tenant could be resolved with an HTTP 400, before
    #: the view runs at all. If ``False``, the request proceeds with no
    #: tenant bound — tenant-scoped managers then return empty querysets
    #: rather than raising, so views must explicitly handle (or
    #: deliberately allow) the no-tenant case, e.g. via
    #: ``IsTenantMember`` or a public, non-tenant-scoped endpoint.
    "STRICT": True,
    #: Cache key prefix used by ``drf_multitenant.cache`` before the
    #: per-tenant segment.
    "CACHE_KEY_PREFIX": "tenant",
    #: Name of the Django cache backend (from ``CACHES``) used by
    #: ``get_tenant_cache()`` when no explicit alias is given.
    "CACHE_ALIAS": "default",
}

_TYPE_CHECKS: Final[dict[str, type | tuple[type, ...]]] = {
    "TENANT_MODEL": (str, type(None)),
    "TENANT_FIELD": str,
    "RESOLVER": str,
    "TENANT_HEADER": str,
    "USER_TENANT_ATTR": str,
    "STRICT": bool,
    "CACHE_KEY_PREFIX": str,
    "CACHE_ALIAS": str,
}


class _MultitenantSettings:
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
        if not merged["TENANT_FIELD"]:
            raise ImproperlyConfigured(
                f"'{USER_SETTINGS_NAME}[\"TENANT_FIELD\"]' must not be empty."
            )
        return merged

    def __getitem__(self, key: str) -> Any:
        if key not in DEFAULTS:
            raise KeyError(f"Invalid setting: {key!r}. Valid keys are: {sorted(DEFAULTS)}.")
        return self._user_settings[key]

    def _on_setting_changed(self, *, sender: Any, setting: str, **kwargs: Any) -> None:
        if setting == USER_SETTINGS_NAME:
            self.__dict__.pop("_user_settings", None)


app_settings = _MultitenantSettings()


def get_setting(key: str) -> Any:
    """Return the effective value of a single package setting.

    Args:
        key: One of the keys documented in :data:`DEFAULTS`.

    Returns:
        The user-configured value if present in the ``MULTITENANT``
        Django setting, otherwise the default.

    Raises:
        KeyError: If ``key`` is not a recognized setting name.
        django.core.exceptions.ImproperlyConfigured: If the
            ``MULTITENANT`` setting is malformed.
    """
    return app_settings[key]
