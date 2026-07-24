"""DRF permission for restricting access to an upload's owner."""

from __future__ import annotations

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from drf_file_pipeline.models import FileUpload


class IsUploadOwner(BasePermission):
    """Object-level permission: only the upload's owner may access it.

    Uploads created by an unauthenticated request (``owner is None``)
    are accessible to anyone holding the upload's id — there is no
    owner to restrict to, and requiring authentication for anonymous
    upload flows is a separate, view-level decision
    (``permission_classes``), not this permission's concern.
    """

    def has_object_permission(self, request: Request, view: APIView, obj: FileUpload) -> bool:
        if obj.owner_id is None:
            return True
        return bool(obj.owner_id == getattr(request.user, "pk", None))
