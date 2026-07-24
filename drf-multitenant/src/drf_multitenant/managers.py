"""Automatic tenant-scoped querysets.

:class:`TenantManager` is the default manager tenant-scoped models
should use as ``objects`` — every query it builds is automatically
filtered to the current tenant (see :mod:`drf_multitenant.context`),
so an accidental ``Model.objects.all()`` anywhere in the codebase can
never leak another tenant's rows. :meth:`TenantQuerySet.unscoped` is the
explicit, greppable escape hatch for the rare legitimate cross-tenant
query (an internal admin dashboard, a data-migration script).
"""

from __future__ import annotations

import logging
from typing import Any, TypeVar

from django.db import models

from drf_multitenant.context import get_current_tenant
from drf_multitenant.settings import get_setting

logger = logging.getLogger("drf_multitenant")

_ModelT = TypeVar("_ModelT", bound=models.Model)


class TenantQuerySet(models.QuerySet[_ModelT]):
    """A queryset that filters to the current tenant unless explicitly told not to."""

    def scoped_to_current_tenant(self) -> TenantQuerySet[_ModelT]:
        """Return this queryset filtered to the current tenant context.

        Returns an empty queryset (never raises) when no tenant is set —
        this keeps ``Model.objects.all()`` safe to construct at any time,
        including at import time (e.g. a serializer field's
        ``queryset=Model.objects.all()`` built in a class body, long
        before any request context exists). Enforcing that a tenant
        *must* be resolvable is a request-level concern; see
        ``MULTITENANT["STRICT"]`` and
        :class:`~drf_multitenant.middleware.TenantMiddleware`, which
        rejects the request itself before any view or queryset code runs.
        """
        tenant = get_current_tenant()
        if tenant is None:
            return self.none()
        field = get_setting("TENANT_FIELD")
        return self.filter(**{field: tenant})

    def unscoped(self) -> TenantQuerySet[_ModelT]:
        """Return this queryset with no tenant filtering applied at all.

        This is the explicit, intentionally-named escape hatch for
        legitimate cross-tenant access. Every call is logged at
        ``WARNING`` level so unexpected/accidental use is visible in
        logs and greppable in code review.
        """
        logger.warning(
            "Unscoped (cross-tenant) query issued against %s.",
            self.model.__name__,
            stack_info=True,
        )
        return self


class TenantManager(models.Manager[_ModelT]):
    """Default manager for tenant-scoped models: automatically filters to the current tenant."""

    def get_queryset(self) -> TenantQuerySet[_ModelT]:
        qs: TenantQuerySet[_ModelT] = TenantQuerySet(self.model, using=self._db)
        return qs.scoped_to_current_tenant()

    def unscoped(self) -> TenantQuerySet[_ModelT]:
        """Shortcut for ``TenantManager().get_queryset().unscoped()`` without the double-filter.

        Builds the queryset directly rather than via
        :meth:`get_queryset` so the (logged) unscoped access doesn't
        first apply and then discard a tenant filter.
        """
        qs: TenantQuerySet[_ModelT] = TenantQuerySet(self.model, using=self._db)
        return qs.unscoped()


def tenant_pk(tenant: Any) -> Any:
    """Return the primary key of a tenant instance, or the value itself if it's already a pk.

    Accepts either a tenant model instance or a raw pk value, so code
    comparing "the tenant on this row" to "the current tenant" doesn't
    need to care which form either side is in.
    """
    return getattr(tenant, "pk", tenant)
