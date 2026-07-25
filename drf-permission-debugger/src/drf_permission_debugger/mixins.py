"""``PermissionDebugMixin``: records why a permission check granted or denied.

Mix into any ``APIView``/``GenericAPIView``/viewset. It overrides
``check_permissions``/``check_object_permissions`` to record each
configured permission class's outcome - calling DRF's own
``has_permission``/``has_object_permission`` in exactly the order and
with exactly the early-exit-on-first-denial behavior
``APIView.check_permissions``/``check_object_permissions`` already
have, so mixing this in never changes who is authorized to do what.
The recorded trace is exposed as a response header (and optionally the
response body on a denial) only when the ``PERMISSION_DEBUGGER``
setting is enabled - see ``docs/security.md`` for why that's opt-in and
staff-restricted by default.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from drf_permission_debugger.settings import get_setting
from drf_permission_debugger.tracing import PermissionCheckResult, PermissionTrace

if TYPE_CHECKING:
    from rest_framework.permissions import _SupportsHasPermission
    from rest_framework.request import Request
    from rest_framework.response import Response


def get_permission_trace(view: Any) -> PermissionTrace | None:
    """Return the :class:`~drf_permission_debugger.tracing.PermissionTrace` recorded on ``view``.

    Returns ``None`` if ``view`` doesn't mix in
    :class:`PermissionDebugMixin`, or no permission check has run yet
    (e.g. called before ``dispatch()``).
    """
    return getattr(view, "_permission_trace", None)


def _is_debugging_authorized(request: Request) -> bool:
    if not get_setting("ENABLED"):
        return False
    if not get_setting("RESTRICT_TO_STAFF"):
        return True
    user = getattr(request, "user", None)
    return bool(user and user.is_authenticated and user.is_staff)


class PermissionDebugMixin:
    """Records a :class:`~drf_permission_debugger.tracing.PermissionTrace` for each request."""

    def _record_check(
        self,
        trace: PermissionTrace,
        permission: _SupportsHasPermission,
        granted: bool,
        *,
        object_level: bool,
    ) -> None:
        message = getattr(permission, "message", None) if not granted else None
        code = getattr(permission, "code", None) if not granted else None
        trace.results.append(
            PermissionCheckResult(
                permission_class=permission.__class__.__name__,
                granted=granted,
                object_level=object_level,
                message=str(message) if message is not None else None,
                code=str(code) if code is not None else None,
            )
        )

    def check_permissions(self, request: Request) -> None:
        """Same behavior as ``APIView.check_permissions``, plus trace recording."""
        trace = get_permission_trace(self) or PermissionTrace()
        self._permission_trace = trace
        for permission in self.get_permissions():  # type: ignore[attr-defined]
            granted = permission.has_permission(request, self)
            self._record_check(trace, permission, granted, object_level=False)
            if not granted:
                self.permission_denied(  # type: ignore[attr-defined]
                    request,
                    message=getattr(permission, "message", None),
                    code=getattr(permission, "code", None),
                )

    def check_object_permissions(self, request: Request, obj: Any) -> None:
        """Same behavior as ``APIView.check_object_permissions``, plus trace recording."""
        trace = get_permission_trace(self) or PermissionTrace()
        self._permission_trace = trace
        for permission in self.get_permissions():  # type: ignore[attr-defined]
            granted = permission.has_object_permission(request, self, obj)
            self._record_check(trace, permission, granted, object_level=True)
            if not granted:
                self.permission_denied(  # type: ignore[attr-defined]
                    request,
                    message=getattr(permission, "message", None),
                    code=getattr(permission, "code", None),
                )

    def finalize_response(
        self, request: Request, response: Response, *args: Any, **kwargs: Any
    ) -> Response:
        """Attach the recorded trace to the response, if debugging is authorized."""
        response = super().finalize_response(  # type: ignore[misc]
            request, response, *args, **kwargs
        )
        trace = get_permission_trace(self)
        if not trace or not trace.results or not _is_debugging_authorized(request):
            return response

        response[get_setting("HEADER_NAME")] = trace.as_header_value()
        if (
            get_setting("INCLUDE_IN_RESPONSE_BODY")
            and not trace.all_granted
            and isinstance(response.data, dict)
        ):
            response.data["permission_trace"] = trace.as_dict()
        return response
