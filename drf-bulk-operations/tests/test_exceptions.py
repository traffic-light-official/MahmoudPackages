"""Tests for :mod:`drf_bulk_operations.exceptions`."""

from __future__ import annotations

from rest_framework import status

from drf_bulk_operations.exceptions import (
    BatchSizeExceededError,
    BulkOperationError,
    MissingLookupFieldError,
    NotAListError,
    ObjectNotFoundError,
)


class TestNotAListError:
    def test_status_code_is_400(self) -> None:
        assert NotAListError(dict).status_code == status.HTTP_400_BAD_REQUEST

    def test_message_names_the_received_type(self) -> None:
        exc = NotAListError(dict)
        assert "dict" in str(exc)


class TestBatchSizeExceededError:
    def test_status_code_is_400(self) -> None:
        assert BatchSizeExceededError(150, 100).status_code == status.HTTP_400_BAD_REQUEST

    def test_message_names_submitted_and_max(self) -> None:
        exc = BatchSizeExceededError(150, 100)
        assert "150" in str(exc)
        assert "100" in str(exc)


class TestMissingLookupFieldError:
    def test_message_names_the_lookup_field(self) -> None:
        exc = MissingLookupFieldError("id")
        assert "'id'" in str(exc)


class TestObjectNotFoundError:
    def test_message_names_the_lookup_field_and_value(self) -> None:
        exc = ObjectNotFoundError("id", 42)
        assert "id" in str(exc)
        assert "42" in str(exc)


class TestBulkOperationErrorIsBase:
    def test_every_exception_is_a_bulk_operation_error(self) -> None:
        assert issubclass(NotAListError, BulkOperationError)
        assert issubclass(BatchSizeExceededError, BulkOperationError)
        assert issubclass(MissingLookupFieldError, BulkOperationError)
        assert issubclass(ObjectNotFoundError, BulkOperationError)
