"""Built-in tenant resolvers: ``(request) -> tenant | None`` callables used by
:class:`~drf_multitenant.middleware.TenantMiddleware`.

Configure which one runs via ``MULTITENANT["RESOLVER"]`` (a dotted path),
or write your own with the same signature — it can do anything (look up
a header, parse a subdomain, read the authenticated user, hit a lookup
table) as long as it returns a tenant model instance or ``None``.
"""

from __future__ import annotations

from typing import Any

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest
from django.utils.module_loading import import_string

from drf_multitenant.settings import get_setting


def header_resolver(request: HttpRequest) -> Any | None:
    """Resolve the tenant from a request header (default: ``X-Tenant-ID``).

    The header value is looked up as the tenant model's primary key.
    Returns ``None`` if the header is absent or no matching tenant
    exists (never raises — an unresolved tenant is a request-level
    concern for the middleware/view to decide how to handle).
    """
    header_name = get_setting("TENANT_HEADER")
    meta_key = "HTTP_" + header_name.upper().replace("-", "_")
    tenant_id = request.META.get(meta_key)
    if not tenant_id:
        return None
    return _get_tenant_by_pk(tenant_id)


def subdomain_resolver(request: HttpRequest) -> Any | None:
    """Resolve the tenant from the leftmost label of the request's host.

    ``acme.example.com`` resolves against the tenant model's ``slug``
    field. Returns ``None`` if the host has no subdomain (e.g. a bare
    ``example.com``) or no matching tenant exists.
    """
    host = request.get_host().split(":")[0]
    labels = host.split(".")
    if len(labels) < 3:
        return None
    subdomain = labels[0]
    model = _tenant_model()
    return model._default_manager.filter(slug=subdomain).first()


def user_attr_resolver(request: HttpRequest) -> Any | None:
    """Resolve the tenant from an attribute on the authenticated user.

    Reads ``MULTITENANT["USER_TENANT_ATTR"]`` (default ``"tenant"``) off
    ``request.user``. Returns ``None`` if the user is unauthenticated or
    has no such attribute set.
    """
    user = getattr(request, "user", None)
    if user is None or not getattr(user, "is_authenticated", False):
        return None
    attr = get_setting("USER_TENANT_ATTR")
    return getattr(user, attr, None)


def resolve_tenant(request: HttpRequest) -> Any | None:
    """Resolve the current tenant using the configured ``RESOLVER`` setting."""
    resolver = import_string(get_setting("RESOLVER"))
    result: Any | None = resolver(request)
    return result


def _tenant_model() -> Any:
    dotted_path = get_setting("TENANT_MODEL")
    if not dotted_path:
        raise ImproperlyConfigured(
            "MULTITENANT['TENANT_MODEL'] must be set to \"app_label.ModelName\" "
            "to use header_resolver or subdomain_resolver."
        )
    return apps.get_model(dotted_path)


def _get_tenant_by_pk(pk: Any) -> Any | None:
    model = _tenant_model()
    return model._default_manager.filter(pk=pk).first()
