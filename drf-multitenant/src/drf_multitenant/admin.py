"""A ``ModelAdmin`` mixin that scopes the Django admin to the current tenant.

Superusers see every tenant's rows (the admin is assumed to be a
trusted, cross-tenant surface for them); everyone else only sees rows
belonging to the tenant resolved for their request (see
:class:`~drf_multitenant.middleware.TenantMiddleware` — the admin site
goes through the same middleware stack as any other view).
"""

from __future__ import annotations

from typing import Any

from django.contrib import admin
from django.http import HttpRequest

from drf_multitenant.context import get_current_tenant
from drf_multitenant.settings import get_setting


class TenantAdminMixin(admin.ModelAdmin):  # type: ignore[type-arg]
    """Filters the admin changelist/lookup querysets to the current tenant."""

    def get_queryset(self, request: HttpRequest) -> Any:
        # Bypass the model's default (auto-scoping) manager entirely —
        # the admin needs to decide scoping itself: unfiltered for
        # superusers, explicitly filtered otherwise.
        qs = self.model.all_tenants.all()
        if request.user.is_superuser:
            return qs
        tenant = get_current_tenant()
        if tenant is None:
            return qs.none()
        field = get_setting("TENANT_FIELD")
        return qs.filter(**{field: tenant})
