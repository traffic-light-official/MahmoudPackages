"""Bulk create/update/delete endpoints for Django REST Framework ViewSets.

DRF's own mixins handle exactly one object per request - there's no
built-in way to create, update, or delete many objects in a single
round trip. This package adds ``bulk_create``/``bulk_update``/
``bulk_partial_update``/``bulk_destroy`` actions (mix in only the ones
you need, or use :class:`~drf_bulk_operations.viewsets.BulkModelViewSet`
for all four at once), each accepting a JSON list body and validating/
saving every item.

Two operating modes, controlled by the ``ATOMIC`` Django setting: fully
atomic (default - validate everything first, then save everything in
one transaction, so a single bad item aborts the whole batch with no
partial writes) or non-atomic (every item is attempted independently,
with a structured per-item report of what succeeded and what didn't).
See ``docs/architecture.md`` for the exact semantics of each mode.

This package defines no models of its own - it only adds behavior to
model-backed viewsets you already have.
"""

from __future__ import annotations

from drf_bulk_operations.exceptions import (
    BatchSizeExceededError,
    BulkOperationError,
    MissingLookupFieldError,
    NotAListError,
    ObjectNotFoundError,
)
from drf_bulk_operations.mixins import (
    BulkCreateModelMixin,
    BulkDestroyModelMixin,
    BulkPartialUpdateModelMixin,
    BulkUpdateModelMixin,
)
from drf_bulk_operations.results import ItemResult
from drf_bulk_operations.settings import get_setting
from drf_bulk_operations.viewsets import BulkModelViewSet

__version__ = "1.0.0"

__all__ = [
    "BatchSizeExceededError",
    "BulkCreateModelMixin",
    "BulkDestroyModelMixin",
    "BulkModelViewSet",
    "BulkOperationError",
    "BulkPartialUpdateModelMixin",
    "BulkUpdateModelMixin",
    "ItemResult",
    "MissingLookupFieldError",
    "NotAListError",
    "ObjectNotFoundError",
    "__version__",
    "get_setting",
]
