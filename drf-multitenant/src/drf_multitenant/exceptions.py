"""Custom exceptions raised by :mod:`drf_multitenant`."""

from __future__ import annotations

from rest_framework import status
from rest_framework.exceptions import APIException


class MultitenantError(Exception):
    """Base class for all errors raised by this package."""


class NoTenantSetError(MultitenantError):
    """Raised when tenant-scoped data is accessed with no current tenant bound."""


class TenantMismatchError(APIException, MultitenantError):
    """Raised when an object is saved with a tenant different from the current context's.

    Subclasses :class:`rest_framework.exceptions.APIException` so it
    converts to an HTTP response automatically when raised from within
    DRF request handling (view/serializer code); catch it explicitly if
    raised from a non-DRF context (a management command, a Celery task).
    """

    status_code = status.HTTP_409_CONFLICT
    default_detail = "The object's tenant does not match the current tenant context."
    default_code = "tenant_mismatch"


class CrossTenantReferenceError(APIException, MultitenantError):
    """Raised when a serializer write would relate an object to another tenant's data."""

    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Cannot reference an object belonging to a different tenant."
    default_code = "cross_tenant_reference"


class TenantLeakError(MultitenantError):
    """Raised by testing/leak-detection helpers when tenant isolation is violated."""
