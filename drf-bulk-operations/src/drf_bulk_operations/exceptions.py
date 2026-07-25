"""Exceptions raised by :mod:`drf_bulk_operations`."""

from __future__ import annotations

from rest_framework import status
from rest_framework.exceptions import APIException


class BulkOperationError(APIException):
    """Base class for every error this package raises. Never raised directly."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "bulk_operation_error"


class NotAListError(BulkOperationError):
    """Raised when a bulk request body is not a JSON array."""

    default_code = "not_a_list"

    def __init__(self, received_type: type) -> None:
        detail = f"Expected a list of items, got {received_type.__name__}."
        super().__init__(detail=detail, code=self.default_code)


class BatchSizeExceededError(BulkOperationError):
    """Raised when a bulk request submits more items than ``MAX_BATCH_SIZE``."""

    default_code = "batch_size_exceeded"

    def __init__(self, submitted: int, max_batch_size: int) -> None:
        detail = (
            f"Batch of {submitted} item(s) exceeds the maximum of "
            f"{max_batch_size} item(s) per request."
        )
        super().__init__(detail=detail, code=self.default_code)


class MissingLookupFieldError(BulkOperationError):
    """Stored (not raised) as a per-item result when an item has no lookup field."""

    default_code = "missing_lookup_field"

    def __init__(self, lookup_field: str) -> None:
        detail = f"Item is missing the required {lookup_field!r} field."
        super().__init__(detail=detail, code=self.default_code)


class ObjectNotFoundError(BulkOperationError):
    """Stored (not raised) as a per-item result when a lookup value matches no object."""

    default_code = "object_not_found"

    def __init__(self, lookup_field: str, value: object) -> None:
        detail = f"No object found with {lookup_field}={value!r}."
        super().__init__(detail=detail, code=self.default_code)
