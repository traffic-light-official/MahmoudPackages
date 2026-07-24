"""Per-tenant cache key namespacing on top of Django's own cache framework.

No new cache backend is introduced — ``TenantCache`` is a thin wrapper
around whichever backend is configured in ``CACHES`` (``LocMemCache``,
``RedisCache``, ``django-redis``, Memcached, ...), so per-tenant caching
works with whatever your project already uses.
"""

from __future__ import annotations

from typing import Any

from django.core.cache import BaseCache, caches

from drf_multitenant.context import require_current_tenant
from drf_multitenant.managers import tenant_pk
from drf_multitenant.settings import get_setting


def tenant_cache_key(key: str, *, tenant: Any | None = None) -> str:
    """Namespace ``key`` to the current (or given) tenant.

    Args:
        key: The unprefixed cache key.
        tenant: The tenant to namespace by. Defaults to the current
            tenant context.

    Returns:
        ``"<CACHE_KEY_PREFIX>:<tenant pk>:<key>"``.

    Raises:
        drf_multitenant.exceptions.NoTenantSetError: If ``tenant`` isn't
            given and no tenant is set in the current context.
    """
    resolved = tenant if tenant is not None else require_current_tenant()
    prefix = get_setting("CACHE_KEY_PREFIX")
    return f"{prefix}:{tenant_pk(resolved)}:{key}"


class TenantCache:
    """A cache wrapper that automatically namespaces every key to the current tenant.

    Every method mirrors Django's ``BaseCache`` API (``get``, ``set``,
    ``delete``, ``get_or_set``, ``incr``, ``decr``) but rewrites the key
    through :func:`tenant_cache_key` first, so cache entries can never
    collide across tenants regardless of what the caller passes in.
    """

    def __init__(self, alias: str | None = None) -> None:
        self._alias = alias if alias is not None else get_setting("CACHE_ALIAS")

    @property
    def _cache(self) -> BaseCache:
        return caches[self._alias]

    def get(self, key: str, default: Any = None) -> Any:
        return self._cache.get(tenant_cache_key(key), default)

    def set(self, key: str, value: Any, timeout: int | float | None = None) -> None:
        self._cache.set(tenant_cache_key(key), value, timeout)

    def delete(self, key: str) -> None:
        self._cache.delete(tenant_cache_key(key))

    def get_or_set(self, key: str, default: Any, timeout: int | float | None = None) -> Any:
        return self._cache.get_or_set(tenant_cache_key(key), default, timeout)

    def incr(self, key: str, delta: int = 1) -> int:
        result: int = self._cache.incr(tenant_cache_key(key), delta)
        return result

    def decr(self, key: str, delta: int = 1) -> int:
        result: int = self._cache.decr(tenant_cache_key(key), delta)
        return result

    def clear_tenant(self, tenant: Any | None = None) -> None:
        """Not supported by most cache backends (no prefix-scan API); provided for
        completeness where a backend does support it (e.g. via ``delete_pattern``
        on ``django-redis``).

        Raises:
            NotImplementedError: Always, on the default Django cache
                backends, which have no key-enumeration API. Override in
                a subclass if your backend supports pattern deletion.
        """
        raise NotImplementedError(
            "The configured cache backend has no key-enumeration API. "
            "Track tenant cache keys yourself if you need bulk invalidation, "
            "or use a backend (e.g. django-redis) and override this method."
        )


def get_tenant_cache(alias: str | None = None) -> TenantCache:
    """Return a :class:`TenantCache` wrapping the named cache backend (default: ``CACHE_ALIAS``)."""
    return TenantCache(alias)
