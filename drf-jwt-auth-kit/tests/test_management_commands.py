"""Tests for the ``cleanup_expired_tokens`` management command."""

from __future__ import annotations

import datetime as dt
from io import StringIO

import pytest
from django.contrib.auth.models import AbstractUser
from django.core.management import call_command
from django.utils import timezone

from drf_jwt_auth_kit.models import Device, RefreshToken

pytestmark = pytest.mark.django_db


class TestCleanupExpiredTokens:
    def test_deletes_tokens_expired_more_than_a_day_ago(self, user: AbstractUser) -> None:
        device = Device.objects.create(user=user)
        stale = RefreshToken.objects.create(
            device=device, expires_at=timezone.now() - dt.timedelta(days=2)
        )
        recent = RefreshToken.objects.create(
            device=device, expires_at=timezone.now() + dt.timedelta(days=1)
        )
        out = StringIO()

        call_command("cleanup_expired_tokens", stdout=out)

        assert not RefreshToken.objects.filter(pk=stale.pk).exists()
        assert RefreshToken.objects.filter(pk=recent.pk).exists()
        assert "Deleted 1 expired refresh token" in out.getvalue()

    def test_reports_zero_when_nothing_to_delete(self, user: AbstractUser) -> None:
        out = StringIO()

        call_command("cleanup_expired_tokens", stdout=out)

        assert "Deleted 0 expired refresh token" in out.getvalue()
