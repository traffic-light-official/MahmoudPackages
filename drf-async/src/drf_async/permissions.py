"""Async-native permission support.

Existing DRF ``BasePermission`` subclasses keep working unchanged with
:class:`~drf_async.views.AsyncAPIView` - their ``has_permission``/
``has_object_permission`` are bridged via
:func:`drf_async.compat.call_maybe_async`. :class:`BaseAsyncPermission`
is for permission checks that are naturally async themselves (e.g.
calling an external auth service over the network) and would otherwise
have to block the event loop or pay for an unnecessary thread hop.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rest_framework.permissions import BasePermission

from drf_async.compat import call_maybe_async

if TYPE_CHECKING:
    from rest_framework.permissions import _SupportsHasPermission
    from rest_framework.request import Request
    from rest_framework.views import APIView


class BaseAsyncPermission(BasePermission):
    """Base class for a permission whose checks are naturally async.

    Subclasses override ``async def has_permission``/
    ``async def has_object_permission`` instead of the synchronous
    versions. Both default to permitting the request/object, matching
    :class:`rest_framework.permissions.BasePermission`'s own defaults.
    """

    async def has_permission(self, request: Request, view: APIView) -> bool:  # type: ignore[override]
        """Return whether the request should be permitted. Defaults to ``True``."""
        return True

    async def has_object_permission(  # type: ignore[override]
        self, request: Request, view: APIView, obj: Any
    ) -> bool:
        """Return whether the request should be permitted for ``obj``. Defaults to ``True``."""
        return True


async def check_permission(
    permission: _SupportsHasPermission, request: Request, view: APIView
) -> bool:
    """Check one permission instance, bridging sync and async transparently."""
    return bool(await call_maybe_async(permission.has_permission, request, view))


async def check_object_permission(
    permission: _SupportsHasPermission, request: Request, view: APIView, obj: Any
) -> bool:
    """Check one permission instance's object-level check, bridging transparently."""
    return bool(await call_maybe_async(permission.has_object_permission, request, view, obj))
