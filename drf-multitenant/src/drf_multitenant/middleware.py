"""Django middleware that resolves and binds the current tenant for each request."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse

from drf_multitenant.context import reset_current_tenant, set_current_tenant
from drf_multitenant.resolvers import resolve_tenant
from drf_multitenant.settings import get_setting


class TenantMiddleware:
    """Resolves the current tenant for every request and binds it to the tenant context.

    The resolved tenant (or ``None`` if resolution failed) is also
    attached to ``request.tenant`` for convenience in views that want to
    branch on it directly rather than going through
    :func:`~drf_multitenant.context.get_current_tenant`.

    If ``MULTITENANT["STRICT"]`` is ``True`` (the default) and no tenant
    could be resolved, the request is rejected with an HTTP 400 before
    the view runs at all. Set it to ``False`` to allow requests with no
    resolvable tenant through — tenant-scoped querysets will then simply
    return empty results (see :mod:`drf_multitenant.managers`).

    The context is always reset after the response is generated, even
    if a view raises — using a ``try``/``finally`` around
    ``get_response`` — so tenant state never leaks between requests
    sharing the same worker/thread.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        tenant: Any | None = resolve_tenant(request)
        request.tenant = tenant  # type: ignore[attr-defined]

        if tenant is None and get_setting("STRICT"):
            return JsonResponse(
                {"detail": "No tenant could be resolved for this request."}, status=400
            )

        token = set_current_tenant(tenant)
        try:
            return self.get_response(request)
        finally:
            reset_current_tenant(token)
