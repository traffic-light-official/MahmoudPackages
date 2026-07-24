"""A serializer mixin enforcing tenant scoping on writes.

Queryset-level filtering (:class:`~drf_multitenant.managers.TenantManager`)
prevents *reading* another tenant's rows. It does nothing to stop a
client from *writing* a relation to another tenant's object it somehow
already has the primary key of (e.g. a sequential integer id guessed or
leaked elsewhere) — that's what this mixin closes.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from django.db import models
from rest_framework import serializers

from drf_multitenant.context import get_current_tenant
from drf_multitenant.exceptions import CrossTenantReferenceError
from drf_multitenant.managers import tenant_pk
from drf_multitenant.settings import get_setting


class TenantScopedSerializerMixin:
    """Auto-assigns the current tenant on create and rejects cross-tenant relations.

    Mix this into any ``ModelSerializer`` whose model has a tenant
    field. On ``create()``, the current tenant is injected into
    ``validated_data`` if not already present. On ``validate()``, every
    related object in the incoming data (any field value that is itself
    a tenant-scoped model instance, singly or in an iterable) is checked
    against the current tenant.
    """

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        current = get_current_tenant()
        field = get_setting("TENANT_FIELD")
        if current is not None:
            for name, value in attrs.items():
                for related in _iter_model_instances(value):
                    related_tenant_id = getattr(related, f"{field}_id", None)
                    if related_tenant_id is not None and related_tenant_id != tenant_pk(current):
                        raise CrossTenantReferenceError(
                            f"'{name}' references an object belonging to a different tenant."
                        )
        return super().validate(attrs)  # type: ignore[misc, no-any-return]

    def create(self, validated_data: dict[str, Any]) -> Any:
        field = get_setting("TENANT_FIELD")
        current = get_current_tenant()
        if field not in validated_data and current is not None:
            validated_data[field] = current
        return super().create(validated_data)  # type: ignore[misc]


class TenantScopedModelSerializer(TenantScopedSerializerMixin, serializers.ModelSerializer[Any]):
    """Convenience base combining :class:`TenantScopedSerializerMixin` with ``ModelSerializer``."""


def _iter_model_instances(value: Any) -> Iterable[models.Model]:
    if isinstance(value, models.Model):
        yield value
    elif isinstance(value, (list, tuple, models.QuerySet)):
        for item in value:
            if isinstance(item, models.Model):
                yield item
