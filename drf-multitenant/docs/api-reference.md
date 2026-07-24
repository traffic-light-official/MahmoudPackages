# API Reference

Generated in part from source docstrings via
[mkdocstrings](https://mkdocstrings.github.io/).

## Context

### get_current_tenant

::: drf_multitenant.context.get_current_tenant

### require_current_tenant

::: drf_multitenant.context.require_current_tenant

### set_current_tenant

::: drf_multitenant.context.set_current_tenant

### reset_current_tenant

::: drf_multitenant.context.reset_current_tenant

### tenant_context

::: drf_multitenant.context.tenant_context

## Models

### TenantScopedModel

::: drf_multitenant.models.TenantScopedModel

## Managers

### TenantManager

::: drf_multitenant.managers.TenantManager

### TenantQuerySet

::: drf_multitenant.managers.TenantQuerySet

### tenant_pk

::: drf_multitenant.managers.tenant_pk

## Middleware

### TenantMiddleware

::: drf_multitenant.middleware.TenantMiddleware

## Resolvers

### header_resolver

::: drf_multitenant.resolvers.header_resolver

### subdomain_resolver

::: drf_multitenant.resolvers.subdomain_resolver

### user_attr_resolver

::: drf_multitenant.resolvers.user_attr_resolver

### resolve_tenant

::: drf_multitenant.resolvers.resolve_tenant

## Permissions

### IsTenantMember

::: drf_multitenant.permissions.IsTenantMember

## Serializers

### TenantScopedSerializerMixin

::: drf_multitenant.serializers.TenantScopedSerializerMixin

### TenantScopedModelSerializer

::: drf_multitenant.serializers.TenantScopedModelSerializer

## Cache

### tenant_cache_key

::: drf_multitenant.cache.tenant_cache_key

### TenantCache

::: drf_multitenant.cache.TenantCache

### get_tenant_cache

::: drf_multitenant.cache.get_tenant_cache

## Admin

### TenantAdminMixin

::: drf_multitenant.admin.TenantAdminMixin

## Testing

### as_tenant

::: drf_multitenant.testing.as_tenant

### as_no_tenant

::: drf_multitenant.testing.as_no_tenant

### assert_no_cross_tenant_leak

::: drf_multitenant.testing.assert_no_cross_tenant_leak

## Exceptions

### MultitenantError

::: drf_multitenant.exceptions.MultitenantError

### NoTenantSetError

::: drf_multitenant.exceptions.NoTenantSetError

### TenantMismatchError

::: drf_multitenant.exceptions.TenantMismatchError

### CrossTenantReferenceError

::: drf_multitenant.exceptions.CrossTenantReferenceError

### TenantLeakError

::: drf_multitenant.exceptions.TenantLeakError

## Settings

See [Settings](settings.md) for the full list of recognized
`MULTITENANT` keys.
