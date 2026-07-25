"""Static introspection of a view's permission stack, without a live request.

Useful for understanding what a view *would* check before ever sending
it a request - e.g. from a shell, a management command (see
``drf_permission_debugger.management.commands.show_view_permissions``),
or a test asserting a view is guarded by the permission class you
expect.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any

from rest_framework.permissions import BasePermission


@dataclass(frozen=True)
class PermissionDescription:
    """A static description of one permission class, with no live request involved.

    Attributes:
        name: The permission class's name.
        docstring: The class's *own* docstring, or an empty string if
            it doesn't define one itself - deliberately not falling
            back to an inherited docstring (e.g. from
            ``BasePermission``, which has its own generic one), since
            that would show a generic, unhelpful description for an
            undocumented custom permission class instead of correctly
            reporting that it has no docstring of its own.
        checks_object_permission: Whether this class overrides
            ``has_object_permission`` (rather than relying on
            ``BasePermission``'s default, which always grants) - i.e.
            whether it does anything beyond a request-level check.
    """

    name: str
    docstring: str
    checks_object_permission: bool


def describe_permissions(view_class: type) -> list[PermissionDescription]:
    """Describe every permission class configured on ``view_class``.

    Args:
        view_class: A DRF view/viewset class - anything with a
            ``permission_classes`` attribute, the same attribute
            ``APIView.get_permissions()`` reads.

    Returns:
        One :class:`PermissionDescription` per configured permission
        class, in the same order ``permission_classes`` lists them (the
        order DRF checks them in, and the order a denial is found in).
    """
    permission_classes: list[type[BasePermission]] = getattr(view_class, "permission_classes", [])
    return [
        PermissionDescription(
            name=permission_class.__name__,
            docstring=_own_docstring(permission_class),
            checks_object_permission=_overrides_has_object_permission(permission_class),
        )
        for permission_class in permission_classes
    ]


def _own_docstring(cls: type) -> str:
    """Return ``cls``'s own docstring, ignoring any inherited one."""
    raw = cls.__dict__.get("__doc__")
    return inspect.cleandoc(raw) if raw else ""


def _overrides_has_object_permission(permission_class: type[BasePermission]) -> bool:
    return permission_class.has_object_permission is not BasePermission.has_object_permission


def describe_view(view_class: type) -> dict[str, Any]:
    """Describe a view's full permission/authentication/throttle stack.

    Returns:
        A plain dict with ``"permissions"`` (a list of
        :class:`PermissionDescription`), ``"authentication_classes"``,
        and ``"throttle_classes"`` (each a list of class names) -
        suitable for printing or JSON-serializing (after converting
        each ``PermissionDescription`` via ``dataclasses.asdict``).
    """
    return {
        "permissions": describe_permissions(view_class),
        "authentication_classes": [
            cls.__name__ for cls in getattr(view_class, "authentication_classes", [])
        ],
        "throttle_classes": [cls.__name__ for cls in getattr(view_class, "throttle_classes", [])],
    }
