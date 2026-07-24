"""Tests for the cleanup_expired_idempotency_keys management command."""

from __future__ import annotations

from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command

from drf_idempotency.core import get_backend
from drf_idempotency.models import IdempotencyRecord

pytestmark = pytest.mark.django_db


class TestCleanupCommand:
    def test_removes_expired_records(self) -> None:
        backend = get_backend()
        backend.acquire_or_get("expired", "fp", lock_ttl=timedelta(seconds=-1))
        backend.acquire_or_get("active", "fp", lock_ttl=timedelta(seconds=60))

        out = StringIO()
        call_command("cleanup_expired_idempotency_keys", stdout=out)

        assert not IdempotencyRecord.objects.filter(key="expired").exists()
        assert IdempotencyRecord.objects.filter(key="active").exists()
        assert "Removed 1" in out.getvalue()

    def test_quiet_flag_suppresses_output(self) -> None:
        out = StringIO()
        call_command("cleanup_expired_idempotency_keys", quiet=True, stdout=out)
        assert out.getvalue() == ""
