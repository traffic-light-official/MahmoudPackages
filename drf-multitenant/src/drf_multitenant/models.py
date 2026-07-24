"""An abstract base class for tenant-scoped models.

``TenantScopedModel`` does not define the tenant foreign key itself —
the field name is configurable (``MULTITENANT["TENANT_FIELD"]``, default
``"tenant"``), so your concrete model defines its own FK to whatever
your tenant model is::

    class Article(TenantScopedModel):
        tenant = models.ForeignKey("accounts.Tenant", on_delete=models.CASCADE)
        title = models.CharField(max_length=200)

This gets you, for free: ``objects`` automatically filtered to the
current tenant, an explicit ``all_tenants`` escape hatch, and a
``save()`` override that auto-assigns the current tenant on creation
and rejects saving a row under a tenant that doesn't match the current
context.
"""

from __future__ import annotations

from typing import Any

from django.db import models

from drf_multitenant.context import get_current_tenant
from drf_multitenant.exceptions import NoTenantSetError, TenantMismatchError
from drf_multitenant.managers import TenantManager, tenant_pk
from drf_multitenant.settings import get_setting


class TenantScopedModel(models.Model):
    """Abstract base providing automatic tenant scoping and save-time enforcement.

    Attributes:
        objects: A :class:`~drf_multitenant.managers.TenantManager` —
            every query is automatically filtered to the current tenant.
        all_tenants: A plain, unfiltered :class:`django.db.models.Manager`
            — the explicit escape hatch for legitimate cross-tenant
            access (superuser dashboards, data migrations).
    """

    objects: TenantManager[Any] = TenantManager()
    all_tenants: models.Manager[Any] = models.Manager()

    class Meta:
        abstract = True

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Auto-assign the current tenant on creation; reject a tenant mismatch on update.

        Raises:
            drf_multitenant.exceptions.NoTenantSetError: If the instance
                has no tenant assigned and none is set in the current
                context to default to.
            drf_multitenant.exceptions.TenantMismatchError: If the
                instance already has a tenant assigned that differs from
                the current context's tenant.
        """
        field = get_setting("TENANT_FIELD")
        current = get_current_tenant()
        existing_id = getattr(self, f"{field}_id")

        if existing_id is None:
            if current is None:
                raise NoTenantSetError(
                    f"Cannot save a {type(self).__name__} with no tenant assigned and no "
                    f"current tenant set. Assign '{field}' explicitly, or ensure "
                    f"TenantMiddleware (or tenant_context()) has run first."
                )
            setattr(self, field, current)
        elif current is not None and existing_id != tenant_pk(current):
            raise TenantMismatchError(
                f"Refusing to save this {type(self).__name__}: its '{field}' does not "
                f"match the current tenant context."
            )
        super().save(*args, **kwargs)
