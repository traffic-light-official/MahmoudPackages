"""Tests for the database-backed idempotency storage."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from drf_idempotency.backends.database import DatabaseBackend
from drf_idempotency.models import IdempotencyRecord

pytestmark = pytest.mark.django_db


@pytest.fixture
def backend() -> DatabaseBackend:
    return DatabaseBackend()


class TestAcquireOrGet:
    def test_first_acquisition_succeeds(self, backend: DatabaseBackend) -> None:
        result = backend.acquire_or_get("key-1", "fp-1", lock_ttl=timedelta(seconds=30))
        assert result.acquired is True
        assert result.existing is None
        assert IdempotencyRecord.objects.filter(key="key-1").exists()

    def test_second_acquisition_with_active_lock_fails(self, backend: DatabaseBackend) -> None:
        backend.acquire_or_get("key-1", "fp-1", lock_ttl=timedelta(seconds=30))
        result = backend.acquire_or_get("key-1", "fp-1", lock_ttl=timedelta(seconds=30))
        assert result.acquired is False
        assert result.existing is not None
        assert result.existing.status == "in_progress"

    def test_abandoned_lock_past_ttl_is_reclaimed(self, backend: DatabaseBackend) -> None:
        backend.acquire_or_get("key-1", "fp-1", lock_ttl=timedelta(seconds=30))
        IdempotencyRecord.objects.filter(key="key-1").update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )
        result = backend.acquire_or_get("key-1", "fp-2", lock_ttl=timedelta(seconds=30))
        assert result.acquired is True
        record = IdempotencyRecord.objects.get(key="key-1")
        assert record.fingerprint == "fp-2"

    def test_expired_completed_record_is_deleted_and_reacquired(
        self, backend: DatabaseBackend
    ) -> None:
        backend.acquire_or_get("key-1", "fp-1", lock_ttl=timedelta(seconds=30))
        backend.complete(
            "key-1",
            status_code=200,
            headers={},
            body=b"{}",
            ttl=timedelta(seconds=-1),  # already expired
        )
        result = backend.acquire_or_get("key-1", "fp-2", lock_ttl=timedelta(seconds=30))
        assert result.acquired is True

    def test_completed_record_within_ttl_is_returned_as_existing(
        self, backend: DatabaseBackend
    ) -> None:
        backend.acquire_or_get("key-1", "fp-1", lock_ttl=timedelta(seconds=30))
        backend.complete(
            "key-1",
            status_code=201,
            headers={"X-Foo": "bar"},
            body=b'{"ok": true}',
            ttl=timedelta(seconds=60),
        )
        result = backend.acquire_or_get("key-1", "fp-1", lock_ttl=timedelta(seconds=30))
        assert result.acquired is False
        assert result.existing is not None
        assert result.existing.status == "completed"
        assert result.existing.response_status_code == 201
        assert result.existing.response_body == b'{"ok": true}'
        assert result.existing.response_headers == {"X-Foo": "bar"}


class TestComplete:
    def test_stores_response_and_marks_completed(self, backend: DatabaseBackend) -> None:
        backend.acquire_or_get("key-1", "fp-1", lock_ttl=timedelta(seconds=30))
        backend.complete(
            "key-1",
            status_code=200,
            headers={"Content-Type": "application/json"},
            body=b"hello",
            ttl=timedelta(seconds=60),
        )
        record = IdempotencyRecord.objects.get(key="key-1")
        assert record.status == IdempotencyRecord.STATUS_COMPLETED
        assert record.response_status_code == 200
        assert record.completed_at is not None


class TestFail:
    def test_deletes_the_record(self, backend: DatabaseBackend) -> None:
        backend.acquire_or_get("key-1", "fp-1", lock_ttl=timedelta(seconds=30))
        backend.fail("key-1")
        assert not IdempotencyRecord.objects.filter(key="key-1").exists()

    def test_is_a_no_op_for_unknown_key(self, backend: DatabaseBackend) -> None:
        backend.fail("does-not-exist")  # must not raise


class TestGet:
    def test_returns_none_for_unknown_key(self, backend: DatabaseBackend) -> None:
        assert backend.get("does-not-exist") is None

    def test_returns_none_for_expired_key(self, backend: DatabaseBackend) -> None:
        backend.acquire_or_get("key-1", "fp-1", lock_ttl=timedelta(seconds=-1))
        assert backend.get("key-1") is None

    def test_returns_record_for_active_key(self, backend: DatabaseBackend) -> None:
        backend.acquire_or_get("key-1", "fp-1", lock_ttl=timedelta(seconds=30))
        record = backend.get("key-1")
        assert record is not None
        assert record.fingerprint == "fp-1"


class TestCleanupExpired:
    def test_removes_only_expired_records(self, backend: DatabaseBackend) -> None:
        backend.acquire_or_get("expired", "fp", lock_ttl=timedelta(seconds=-1))
        backend.acquire_or_get("active", "fp", lock_ttl=timedelta(seconds=60))
        deleted = backend.cleanup_expired()
        assert deleted == 1
        assert not IdempotencyRecord.objects.filter(key="expired").exists()
        assert IdempotencyRecord.objects.filter(key="active").exists()

    def test_returns_zero_when_nothing_expired(self, backend: DatabaseBackend) -> None:
        backend.acquire_or_get("active", "fp", lock_ttl=timedelta(seconds=60))
        assert backend.cleanup_expired() == 0
