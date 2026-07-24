"""Database-backed idempotency storage.

Uses :class:`~drf_idempotency.models.IdempotencyRecord`, relying on its
unique constraint on ``key`` plus Django's ``get_or_create`` (which
catches the resulting ``IntegrityError`` and re-fetches on a race) for
atomic lock acquisition — no database-specific locking primitives are
required, so this backend works identically on PostgreSQL, MySQL, and
SQLite.
"""

from __future__ import annotations

import base64
from collections.abc import Mapping
from datetime import timedelta
from typing import Any

from django.db import transaction
from django.utils import timezone

from drf_idempotency.backends.base import AcquireResult, BaseBackend, StoredRecord
from drf_idempotency.models import IdempotencyRecord


class DatabaseBackend(BaseBackend):
    """Stores idempotency records in the database via
    :class:`~drf_idempotency.models.IdempotencyRecord`.

    Requires ``"drf_idempotency"`` to be listed in ``INSTALLED_APPS`` and
    migrated (``python manage.py migrate``).
    """

    def acquire_or_get(self, key: str, fingerprint: str, *, lock_ttl: timedelta) -> AcquireResult:
        """See :meth:`drf_idempotency.backends.base.BaseBackend.acquire_or_get`."""
        now = timezone.now()
        with transaction.atomic():
            record, created = IdempotencyRecord.objects.get_or_create(
                key=key,
                defaults={
                    "fingerprint": fingerprint,
                    "status": IdempotencyRecord.STATUS_IN_PROGRESS,
                    "expires_at": now + lock_ttl,
                },
            )
        if created:
            return AcquireResult(acquired=True, existing=None)
        return self._handle_existing(record, fingerprint, now=now, lock_ttl=lock_ttl)

    def _handle_existing(
        self,
        record: IdempotencyRecord,
        fingerprint: str,
        *,
        now: Any,
        lock_ttl: timedelta,
    ) -> AcquireResult:
        if record.expires_at > now:
            return AcquireResult(acquired=False, existing=self._to_stored_record(record))

        # The record has expired. An in-progress lock past its TTL is
        # treated as abandoned (its worker likely crashed) and reclaimed;
        # an expired completed/failed record is deleted and a fresh
        # attempt is made, as if the key had never been used.
        if record.status == IdempotencyRecord.STATUS_IN_PROGRESS:
            reclaimed = IdempotencyRecord.objects.filter(
                pk=record.pk, status=IdempotencyRecord.STATUS_IN_PROGRESS, expires_at__lte=now
            ).update(fingerprint=fingerprint, expires_at=now + lock_ttl, created_at=now)
            if reclaimed:
                return AcquireResult(acquired=True, existing=None)
            record.refresh_from_db()
            return AcquireResult(acquired=False, existing=self._to_stored_record(record))

        deleted, _ = IdempotencyRecord.objects.filter(pk=record.pk, expires_at__lte=now).delete()
        if deleted:
            return self.acquire_or_get(record.key, fingerprint, lock_ttl=lock_ttl)
        record.refresh_from_db()
        return AcquireResult(acquired=False, existing=self._to_stored_record(record))

    def complete(
        self,
        key: str,
        *,
        status_code: int,
        headers: Mapping[str, str],
        body: bytes,
        ttl: timedelta,
    ) -> None:
        """See :meth:`drf_idempotency.backends.base.BaseBackend.complete`."""
        now = timezone.now()
        IdempotencyRecord.objects.filter(key=key).update(
            status=IdempotencyRecord.STATUS_COMPLETED,
            response_status_code=status_code,
            response_headers=dict(headers),
            response_body=base64.b64encode(body).decode("ascii"),
            completed_at=now,
            expires_at=now + ttl,
        )

    def fail(self, key: str) -> None:
        """See :meth:`drf_idempotency.backends.base.BaseBackend.fail`.

        Deletes the record entirely, so the next request using this key
        starts fresh rather than being permanently stuck.
        """
        IdempotencyRecord.objects.filter(key=key).delete()

    def get(self, key: str) -> StoredRecord | None:
        """See :meth:`drf_idempotency.backends.base.BaseBackend.get`."""
        try:
            record = IdempotencyRecord.objects.get(key=key)
        except IdempotencyRecord.DoesNotExist:
            return None
        if record.expires_at <= timezone.now():
            return None
        return self._to_stored_record(record)

    def cleanup_expired(self) -> int:
        """See :meth:`drf_idempotency.backends.base.BaseBackend.cleanup_expired`."""
        deleted, _ = IdempotencyRecord.objects.filter(expires_at__lte=timezone.now()).delete()
        return deleted

    @staticmethod
    def _to_stored_record(record: IdempotencyRecord) -> StoredRecord:
        body = base64.b64decode(record.response_body) if record.response_body else None
        return StoredRecord(
            key=record.key,
            fingerprint=record.fingerprint,
            status=record.status,
            response_status_code=record.response_status_code,
            response_headers=record.response_headers or None,
            response_body=body,
            created_at=record.created_at,
        )
