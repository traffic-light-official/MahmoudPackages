"""A convenience viewset combining every bulk mixin with DRF's own ``ModelViewSet``."""

from __future__ import annotations

from typing import Any

from rest_framework import viewsets

from drf_bulk_operations.mixins import (
    BulkCreateModelMixin,
    BulkDestroyModelMixin,
    BulkPartialUpdateModelMixin,
)


class BulkModelViewSet(
    BulkCreateModelMixin,
    BulkPartialUpdateModelMixin,
    BulkDestroyModelMixin,
    viewsets.ModelViewSet[Any],
):
    """A ``ModelViewSet`` with bulk create/update/partial_update/destroy actions added.

    Equivalent to mixing :class:`~drf_bulk_operations.mixins.BulkCreateModelMixin`,
    :class:`~drf_bulk_operations.mixins.BulkPartialUpdateModelMixin` (which
    already includes :class:`~drf_bulk_operations.mixins.BulkUpdateModelMixin`),
    and :class:`~drf_bulk_operations.mixins.BulkDestroyModelMixin` into your
    own ``ModelViewSet`` subclass yourself - use this directly, or mix in
    only the specific bulk mixins you need (e.g. only
    ``BulkDestroyModelMixin``, for a viewset that only needs bulk deletion).
    """
