"""The current-tenant context: the single source of truth every other
module in this package reads from.

Uses :mod:`contextvars` rather than thread-locals so the current tenant
propagates correctly through ``async def`` views and ``sync_to_async``/
``async_to_sync`` boundaries, which a plain thread-local would not
handle correctly under ASGI.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Any

from drf_multitenant.exceptions import NoTenantSetError

_current_tenant: ContextVar[Any | None] = ContextVar("drf_multitenant_current_tenant", default=None)


def get_current_tenant() -> Any | None:
    """Return the tenant bound to the current context, or ``None`` if none is set."""
    return _current_tenant.get()


def require_current_tenant() -> Any:
    """Return the current tenant, raising if none is set.

    Raises:
        drf_multitenant.exceptions.NoTenantSetError: If no tenant is
            bound to the current context.
    """
    tenant = _current_tenant.get()
    if tenant is None:
        raise NoTenantSetError(
            "No tenant is set on the current context. This usually means "
            "TenantMiddleware did not run, or you're accessing tenant-scoped "
            "data outside of a request (e.g. a management command or a "
            "background task) without calling tenant_context() yourself."
        )
    return tenant


def set_current_tenant(tenant: Any | None) -> Token[Any | None]:
    """Bind ``tenant`` to the current context.

    Returns:
        A token that can be passed to :func:`reset_current_tenant` to
        restore the previous value. Prefer :func:`tenant_context` unless
        you specifically need manual set/reset control (e.g. inside
        middleware, where the reset must happen after ``get_response``).
    """
    return _current_tenant.set(tenant)


def reset_current_tenant(token: Token[Any | None]) -> None:
    """Restore the tenant context to what it was before the matching :func:`set_current_tenant`."""
    _current_tenant.reset(token)


@contextmanager
def tenant_context(tenant: Any | None) -> Iterator[None]:
    """Bind ``tenant`` to the current context for the duration of the ``with`` block.

    Args:
        tenant: The tenant instance (or ``None`` to explicitly clear the
            context, e.g. for cross-tenant admin operations) to bind.

    Example:
        >>> with tenant_context(some_tenant):
        ...     Article.objects.all()  # automatically scoped to some_tenant
    """
    token = _current_tenant.set(tenant)
    try:
        yield
    finally:
        _current_tenant.reset(token)
