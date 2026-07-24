"""DRF permission classes providing defense-in-depth tenant isolation.

``TenantManager`` already prevents a queryset from returning another
tenant's rows, so ``get_object()`` on a properly-scoped viewset can
never 404-vs-403 leak another tenant's existence via a lookup by id —
it simply won't be found. :class:`IsTenantMember` is a second,
independent check for cases where an object arrives by some other path
(a nested serializer write, a custom action operating on a raw pk from
the request body) where the ORM-level filtering wasn't necessarily
applied.
"""

from __future__ import annotations

from typing import Any

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from drf_multitenant.context import get_current_tenant
from drf_multitenant.managers import tenant_pk
from drf_multitenant.settings import get_setting


class IsTenantMember(BasePermission):
    """Require a resolved current tenant, and that any accessed object belongs to it."""

    message = "This object does not belong to your tenant."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return get_current_tenant() is not None

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        current = get_current_tenant()
        if current is None:
            return False
        field = get_setting("TENANT_FIELD")
        obj_tenant_id = getattr(obj, f"{field}_id", None)
        return bool(obj_tenant_id == tenant_pk(current))
