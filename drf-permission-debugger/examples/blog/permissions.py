"""Custom permission classes for the runnable example."""

from __future__ import annotations

from typing import Any

from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """Object-level only: grants everything at the request level."""

    message = "You do not own this article."
    code = "not_owner"

    def has_object_permission(self, request: Any, view: Any, obj: Any) -> bool:
        user = request.user
        return bool(user and user.is_authenticated and obj.owner_id == user.id)
