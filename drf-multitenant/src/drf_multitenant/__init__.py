"""Shared-schema multi-tenancy for Django REST Framework.

Every tenant-scoped model shares one set of database tables; row-level
isolation is enforced automatically at the ORM layer (via
:class:`~drf_multitenant.managers.TenantManager`), reinforced at the
serializer layer (:class:`~drf_multitenant.serializers.TenantScopedSerializerMixin`)
and the permission layer (:class:`~drf_multitenant.permissions.IsTenantMember`),
so a single missed ``.filter(tenant=...)`` call anywhere in application
code doesn't leak data across tenants.

Typical usage::

    from drf_multitenant.models import TenantScopedModel

    class Article(TenantScopedModel):
        tenant = models.ForeignKey("accounts.Tenant", on_delete=models.CASCADE)
        title = models.CharField(max_length=200)

    # settings.py
    MIDDLEWARE = [..., "drf_multitenant.middleware.TenantMiddleware"]
    MULTITENANT = {"TENANT_MODEL": "accounts.Tenant"}
"""

from __future__ import annotations

from drf_multitenant.context import (
    get_current_tenant,
    require_current_tenant,
    reset_current_tenant,
    set_current_tenant,
    tenant_context,
)
from drf_multitenant.exceptions import (
    CrossTenantReferenceError,
    MultitenantError,
    NoTenantSetError,
    TenantLeakError,
    TenantMismatchError,
)

__version__ = "1.0.0"

__all__ = [
    "CrossTenantReferenceError",
    "MultitenantError",
    "NoTenantSetError",
    "TenantLeakError",
    "TenantMismatchError",
    "__version__",
    "get_current_tenant",
    "require_current_tenant",
    "reset_current_tenant",
    "set_current_tenant",
    "tenant_context",
]
