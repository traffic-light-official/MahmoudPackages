"""Tests for idempotency-key status tracking."""

from __future__ import annotations

from datetime import timedelta

import pytest

from drf_idempotency.core import get_backend
from drf_idempotency.status import get_idempotency_status

pytestmark = pytest.mark.django_db


class TestGetIdempotencyStatus:
    def test_unknown_key_returns_none(self) -> None:
        assert get_idempotency_status("never-used") is None

    def test_in_progress_key_returns_in_progress(self) -> None:
        get_backend().acquire_or_get("key-1", "fp", lock_ttl=timedelta(seconds=30))
        assert get_idempotency_status("key-1") == "in_progress"

    def test_completed_key_returns_completed(self) -> None:
        backend = get_backend()
        backend.acquire_or_get("key-1", "fp", lock_ttl=timedelta(seconds=30))
        backend.complete(
            "key-1", status_code=200, headers={}, body=b"{}", ttl=timedelta(seconds=60)
        )
        assert get_idempotency_status("key-1") == "completed"

    def test_failed_and_released_key_returns_none(self) -> None:
        backend = get_backend()
        backend.acquire_or_get("key-1", "fp", lock_ttl=timedelta(seconds=30))
        backend.fail("key-1")
        assert get_idempotency_status("key-1") is None
