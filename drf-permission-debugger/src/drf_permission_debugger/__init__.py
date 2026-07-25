"""Understand exactly why a Django REST Framework permission check granted or denied a request.

DRF's own ``403``/``401`` responses tell you a request was denied, but
not *which* configured permission class denied it, or why, when
``permission_classes`` has more than one entry. This package's
:class:`~drf_permission_debugger.mixins.PermissionDebugMixin` records
each configured permission class's outcome (granted or denied, and its
message/code) for every request - calling DRF's own ``has_permission``/
``has_object_permission`` in exactly the same order and with the same
early-exit-on-first-denial behavior ``APIView`` already has, so mixing
it in never changes who is authorized to do what. The recorded trace
is opt-in and staff-restricted by default (see ``docs/security.md``)
before it's ever exposed over HTTP.

:mod:`~drf_permission_debugger.introspection` additionally answers a
related but different question with no live request at all: "what
would this view check, and does any of it look at the object, not just
the request?" - useful from a shell, a test, or the bundled
``show_view_permissions`` management command.
"""

from __future__ import annotations

from drf_permission_debugger.introspection import (
    PermissionDescription,
    describe_permissions,
    describe_view,
)
from drf_permission_debugger.mixins import PermissionDebugMixin, get_permission_trace
from drf_permission_debugger.settings import get_setting
from drf_permission_debugger.tracing import PermissionCheckResult, PermissionTrace

__version__ = "1.0.0"

__all__ = [
    "PermissionCheckResult",
    "PermissionDebugMixin",
    "PermissionDescription",
    "PermissionTrace",
    "__version__",
    "describe_permissions",
    "describe_view",
    "get_permission_trace",
    "get_setting",
]
