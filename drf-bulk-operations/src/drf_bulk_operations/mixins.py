"""Bulk create/update/destroy action mixins for a DRF ``GenericAPIView``.

Each mixin adds one ``@action``-decorated method, matching the shape of
``rest_framework.mixins`` (whose ``CreateModelMixin``/``UpdateModelMixin``/
``DestroyModelMixin`` these are the bulk equivalent of) - mix into a
``GenericViewSet``/``ModelViewSet`` alongside ``get_serializer``/
``get_queryset``, exactly like DRF's own mixins.

Two modes, controlled by the ``ATOMIC`` setting (see
``docs/settings.md``):

- **Atomic** (default): every item is validated *before* any database
  write. If any item fails, nothing is saved and the response is
  ``400`` with a list of per-item error dicts (empty for items that
  validated fine), mirroring ``ListSerializer.errors``. If every item
  validates, all saves run inside one transaction - a database-level
  failure partway through rolls back the whole batch.
- **Non-atomic**: every item is attempted independently, each save in
  its own savepoint, so one item's failure doesn't affect the others.
  The response is always the structured per-item list (``200``/``201``/
  ``204`` if every item succeeded, ``207 Multi-Status`` if mixed,
  ``400`` if every item failed) - see :func:`drf_bulk_operations.results.build_bulk_response`.
"""

from __future__ import annotations

from typing import Any

from django.db import DatabaseError, transaction
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.request import Request
from rest_framework.response import Response

from drf_bulk_operations.exceptions import (
    BatchSizeExceededError,
    MissingLookupFieldError,
    NotAListError,
    ObjectNotFoundError,
)
from drf_bulk_operations.results import ItemResult, build_bulk_response
from drf_bulk_operations.settings import get_setting


def _validate_batch(data: Any) -> list[Any]:
    """Check that ``data`` is a list within ``MAX_BATCH_SIZE``, or raise."""
    if not isinstance(data, list):
        raise NotAListError(type(data))
    max_batch_size = get_setting("MAX_BATCH_SIZE")
    if len(data) > max_batch_size:
        raise BatchSizeExceededError(len(data), max_batch_size)
    return data


class BulkCreateModelMixin:
    """Adds a ``bulk_create`` action: ``POST .../bulk/`` with a JSON list body.

    Uses its own dedicated URL rather than sharing one path with the
    other bulk mixins across HTTP methods: DRF's router creates one
    ``Route`` per ``@action``-decorated method, keyed only by its
    ``url_path`` - two independently decorated actions that happen to
    share a ``url_path`` produce two colliding URL patterns, and only
    the first one registered is ever actually reachable (the others
    404/405 silently). Giving every bulk mixin its own path keeps any
    subset of these mixins safely composable with no coordination
    required between them - see ``docs/architecture.md``.
    """

    @action(detail=False, methods=["post"], url_path="bulk")
    def bulk_create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Create every item in the request body's list."""
        items = _validate_batch(request.data)
        if get_setting("ATOMIC"):
            return self._bulk_create_atomic(items)
        return self._bulk_create_non_atomic(items)

    def perform_create(self, serializer: Any) -> None:
        """Save one validated serializer. Matches ``CreateModelMixin.perform_create``."""
        serializer.save()

    def _bulk_create_non_atomic(self, items: list[Any]) -> Response:
        results: list[ItemResult] = []
        for index, data in enumerate(items):
            serializer = self.get_serializer(data=data)  # type: ignore[attr-defined]
            if not serializer.is_valid():
                results.append(ItemResult(index, success=False, errors=serializer.errors))
                continue
            try:
                with transaction.atomic():
                    self.perform_create(serializer)
            except DatabaseError as exc:
                results.append(
                    ItemResult(index, success=False, errors={"non_field_errors": [str(exc)]})
                )
                continue
            results.append(ItemResult(index, success=True, data=serializer.data))
        return build_bulk_response(results, all_success_status=status.HTTP_201_CREATED)

    def _bulk_create_atomic(self, items: list[Any]) -> Response:
        serializers: list[Any] = []
        errors: list[Any] = []
        any_invalid = False
        for data in items:
            serializer = self.get_serializer(data=data)  # type: ignore[attr-defined]
            valid = serializer.is_valid()
            serializers.append(serializer)
            errors.append({} if valid else serializer.errors)
            any_invalid = any_invalid or not valid
        if any_invalid:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            with transaction.atomic():
                for serializer in serializers:
                    self.perform_create(serializer)
        except DatabaseError as exc:
            return Response(
                {"detail": f"Batch rolled back: {exc}"}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            [serializer.data for serializer in serializers], status=status.HTTP_201_CREATED
        )


class BulkUpdateModelMixin:
    """Adds a ``bulk_update`` action: ``PUT .../bulk-update/`` with a JSON list body.

    Each item must include the view's ``bulk_lookup_field`` (``"id"`` by
    default) identifying which existing object it updates; every other
    key is passed to the serializer as the update data.
    """

    #: The field each bulk item uses to identify its target object.
    bulk_lookup_field = "id"

    @action(detail=False, methods=["put"], url_path="bulk-update")
    def bulk_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Fully update every item in the request body's list."""
        return self._bulk_update(request, partial=False)

    def perform_update(self, serializer: Any) -> None:
        """Save one validated serializer. Matches ``UpdateModelMixin.perform_update``."""
        serializer.save()

    def _resolve_instances(self, items: list[Any], lookup_field: str) -> list[Any]:
        """Resolve each item to its target instance, or an unraised error instance."""
        lookup_values: list[Any] = []
        for item in items:
            if isinstance(item, dict) and lookup_field in item:
                lookup_values.append(item[lookup_field])
            else:
                lookup_values.append(None)

        queryset = self.filter_queryset(self.get_queryset())  # type: ignore[attr-defined]
        present_values = [value for value in lookup_values if value is not None]
        found = {
            getattr(obj, lookup_field): obj
            for obj in queryset.filter(**{f"{lookup_field}__in": present_values})
        }

        resolved: list[Any] = []
        for value in lookup_values:
            if value is None:
                resolved.append(MissingLookupFieldError(lookup_field))
                continue
            instance = found.get(value)
            if instance is None:
                resolved.append(ObjectNotFoundError(lookup_field, value))
                continue
            self.check_object_permissions(self.request, instance)  # type: ignore[attr-defined]
            resolved.append(instance)
        return resolved

    def _bulk_update(self, request: Request, *, partial: bool) -> Response:
        items = _validate_batch(request.data)
        lookup_field = self.bulk_lookup_field
        if get_setting("ATOMIC"):
            return self._bulk_update_atomic(items, lookup_field, partial=partial)
        return self._bulk_update_non_atomic(items, lookup_field, partial=partial)

    def _bulk_update_non_atomic(
        self, items: list[Any], lookup_field: str, *, partial: bool
    ) -> Response:
        instances_or_errors = self._resolve_instances(items, lookup_field)
        results: list[ItemResult] = []
        for index, (item, instance_or_error) in enumerate(
            zip(items, instances_or_errors, strict=True)
        ):
            if isinstance(instance_or_error, APIException):
                results.append(
                    ItemResult(index, success=False, errors={"detail": instance_or_error.detail})
                )
                continue
            data = {key: value for key, value in item.items() if key != lookup_field}
            serializer = self.get_serializer(  # type: ignore[attr-defined]
                instance_or_error, data=data, partial=partial
            )
            if not serializer.is_valid():
                results.append(ItemResult(index, success=False, errors=serializer.errors))
                continue
            try:
                with transaction.atomic():
                    self.perform_update(serializer)
            except DatabaseError as exc:
                results.append(
                    ItemResult(index, success=False, errors={"non_field_errors": [str(exc)]})
                )
                continue
            results.append(ItemResult(index, success=True, data=serializer.data))
        return build_bulk_response(results, all_success_status=status.HTTP_200_OK)

    def _bulk_update_atomic(
        self, items: list[Any], lookup_field: str, *, partial: bool
    ) -> Response:
        instances_or_errors = self._resolve_instances(items, lookup_field)
        serializers: list[Any] = []
        errors: list[Any] = []
        any_invalid = False
        for item, instance_or_error in zip(items, instances_or_errors, strict=True):
            if isinstance(instance_or_error, APIException):
                errors.append({"detail": instance_or_error.detail})
                serializers.append(None)
                any_invalid = True
                continue
            data = {key: value for key, value in item.items() if key != lookup_field}
            serializer = self.get_serializer(  # type: ignore[attr-defined]
                instance_or_error, data=data, partial=partial
            )
            valid = serializer.is_valid()
            serializers.append(serializer)
            errors.append({} if valid else serializer.errors)
            any_invalid = any_invalid or not valid
        if any_invalid:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            with transaction.atomic():
                for serializer in serializers:
                    self.perform_update(serializer)
        except DatabaseError as exc:
            return Response(
                {"detail": f"Batch rolled back: {exc}"}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response([serializer.data for serializer in serializers], status=status.HTTP_200_OK)


class BulkPartialUpdateModelMixin(BulkUpdateModelMixin):
    """Adds a ``bulk_partial_update`` action: ``PATCH .../bulk-partial-update/``."""

    @action(detail=False, methods=["patch"], url_path="bulk-partial-update")
    def bulk_partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Partially update every item in the request body's list."""
        return self._bulk_update(request, partial=True)


class BulkDestroyModelMixin:
    """Adds a ``bulk_destroy`` action: ``DELETE .../bulk-delete/`` with a JSON list of ID values."""

    #: The field each bulk item value is matched against.
    bulk_lookup_field = "id"

    @action(detail=False, methods=["delete"], url_path="bulk-delete")
    def bulk_destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delete every object identified in the request body's list of ID values."""
        ids = _validate_batch(request.data)
        lookup_field = self.bulk_lookup_field
        if get_setting("ATOMIC"):
            return self._bulk_destroy_atomic(ids, lookup_field)
        return self._bulk_destroy_non_atomic(ids, lookup_field)

    def perform_destroy(self, instance: Any) -> None:
        """Delete one instance. Matches ``DestroyModelMixin.perform_destroy``."""
        instance.delete()

    def _resolve_instances_by_id(self, ids: list[Any], lookup_field: str) -> list[Any]:
        queryset = self.filter_queryset(self.get_queryset())  # type: ignore[attr-defined]
        found = {
            getattr(obj, lookup_field): obj
            for obj in queryset.filter(**{f"{lookup_field}__in": ids})
        }
        resolved: list[Any] = []
        for value in ids:
            instance = found.get(value)
            if instance is None:
                resolved.append(ObjectNotFoundError(lookup_field, value))
                continue
            self.check_object_permissions(self.request, instance)  # type: ignore[attr-defined]
            resolved.append(instance)
        return resolved

    def _bulk_destroy_non_atomic(self, ids: list[Any], lookup_field: str) -> Response:
        instances_or_errors = self._resolve_instances_by_id(ids, lookup_field)
        results: list[ItemResult] = []
        for index, instance_or_error in enumerate(instances_or_errors):
            if isinstance(instance_or_error, APIException):
                results.append(
                    ItemResult(index, success=False, errors={"detail": instance_or_error.detail})
                )
                continue
            try:
                with transaction.atomic():
                    self.perform_destroy(instance_or_error)
            except DatabaseError as exc:
                results.append(
                    ItemResult(index, success=False, errors={"non_field_errors": [str(exc)]})
                )
                continue
            results.append(ItemResult(index, success=True))
        return build_bulk_response(
            results, all_success_status=status.HTTP_204_NO_CONTENT, empty_success_body=True
        )

    def _bulk_destroy_atomic(self, ids: list[Any], lookup_field: str) -> Response:
        instances_or_errors = self._resolve_instances_by_id(ids, lookup_field)
        errors: list[Any] = []
        any_invalid = False
        for instance_or_error in instances_or_errors:
            if isinstance(instance_or_error, APIException):
                errors.append({"detail": instance_or_error.detail})
                any_invalid = True
            else:
                errors.append({})
        if any_invalid:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            with transaction.atomic():
                for instance in instances_or_errors:
                    self.perform_destroy(instance)
        except DatabaseError as exc:
            return Response(
                {"detail": f"Batch rolled back: {exc}"}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
