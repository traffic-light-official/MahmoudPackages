"""Tests for :mod:`drf_jwt_auth_kit.models`."""

from __future__ import annotations

import datetime as dt

import pytest
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

from drf_jwt_auth_kit.models import Device, LoginHistory, RefreshToken, TOTPDevice

pytestmark = pytest.mark.django_db


class TestDevice:
    def test_is_active_by_default(self, user: AbstractUser) -> None:
        device = Device.objects.create(user=user)

        assert device.is_active is True

    def test_is_active_false_once_revoked(self, user: AbstractUser) -> None:
        device = Device.objects.create(
            user=user, revoked_at=timezone.now(), revoked_reason="logout"
        )

        assert device.is_active is False

    def test_str_uses_label_when_present(self, user: AbstractUser) -> None:
        device = Device.objects.create(user=user, label="My Phone")

        assert str(device) == "My Phone"

    def test_str_falls_back_to_id_when_no_label(self, user: AbstractUser) -> None:
        device = Device.objects.create(user=user)

        assert str(device.id) in str(device)


class TestRefreshToken:
    def test_is_active_by_default(self, user: AbstractUser) -> None:
        device = Device.objects.create(user=user)
        token = RefreshToken.objects.create(
            device=device, expires_at=timezone.now() + dt.timedelta(days=1)
        )

        assert token.is_active is True

    def test_is_active_false_once_revoked(self, user: AbstractUser) -> None:
        device = Device.objects.create(user=user)
        token = RefreshToken.objects.create(
            device=device,
            expires_at=timezone.now() + dt.timedelta(days=1),
            revoked_at=timezone.now(),
            revoked_reason="rotated",
        )

        assert token.is_active is False

    def test_replaced_by_links_the_rotation_chain(self, user: AbstractUser) -> None:
        device = Device.objects.create(user=user)
        first = RefreshToken.objects.create(
            device=device, expires_at=timezone.now() + dt.timedelta(days=1)
        )
        second = RefreshToken.objects.create(
            device=device, expires_at=timezone.now() + dt.timedelta(days=1)
        )
        first.replaced_by = second
        first.save(update_fields=["replaced_by"])

        first.refresh_from_db()
        assert first.replaced_by == second
        assert second.replaces == first


class TestLoginHistory:
    def test_str_includes_outcome(self, user: AbstractUser) -> None:
        success = LoginHistory.objects.create(user=user, username_attempted="ada", success=True)
        failure = LoginHistory.objects.create(
            user=None,
            username_attempted="unknown",
            success=False,
            failure_reason="invalid_credentials",
        )

        assert "success" in str(success)
        assert "invalid_credentials" in str(failure)

    def test_user_can_be_null_for_unknown_usernames(self) -> None:
        history = LoginHistory.objects.create(user=None, username_attempted="ghost", success=False)

        assert history.user is None


class TestTOTPDevice:
    def test_str_reflects_confirmation_state(self, user: AbstractUser) -> None:
        pending = TOTPDevice.objects.create(user=user, secret="ABCDEFGH")

        assert "pending" in str(pending)

        pending.confirmed = True
        pending.save(update_fields=["confirmed"])
        assert "confirmed" in str(pending)
