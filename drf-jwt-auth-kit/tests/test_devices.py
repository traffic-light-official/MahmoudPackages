"""Tests for :mod:`drf_jwt_auth_kit.devices`."""

from __future__ import annotations

import datetime as dt

import pytest
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from drf_jwt_auth_kit.devices import create_device, revoke_all_devices, revoke_device, touch_device
from drf_jwt_auth_kit.models import Device, RefreshToken

pytestmark = pytest.mark.django_db


class TestCreateDevice:
    def test_creates_a_device_with_request_metadata(
        self, user: AbstractUser, api_rf: APIRequestFactory
    ) -> None:
        request = api_rf.post(
            "/auth/login/", HTTP_USER_AGENT="pytest-agent", REMOTE_ADDR="203.0.113.5"
        )

        device = create_device(user=user, request=request, label="My Laptop")

        assert device.user_id == user.pk
        assert device.label == "My Laptop"
        assert device.user_agent == "pytest-agent"
        assert device.created_ip == "203.0.113.5"
        assert device.is_active is True

    def test_prefers_x_forwarded_for_over_remote_addr(
        self, user: AbstractUser, api_rf: APIRequestFactory
    ) -> None:
        request = api_rf.post(
            "/auth/login/",
            REMOTE_ADDR="10.0.0.1",
            HTTP_X_FORWARDED_FOR="198.51.100.7, 10.0.0.1",
        )

        device = create_device(user=user, request=request)

        assert device.created_ip == "198.51.100.7"

    def test_works_without_a_request(self, user: AbstractUser) -> None:
        device = create_device(user=user, request=None, label="CLI")

        assert device.user_agent == ""
        assert device.created_ip is None


class TestTouchDevice:
    def test_updates_last_used_at(self, user: AbstractUser) -> None:
        device = Device.objects.create(user=user)
        original = device.last_used_at

        device.last_used_at = original - dt.timedelta(hours=1)
        device.save(update_fields=["last_used_at"])

        touch_device(device)
        device.refresh_from_db()

        assert device.last_used_at > original - dt.timedelta(hours=1)


class TestRevokeDevice:
    def test_marks_device_revoked(self, user: AbstractUser) -> None:
        device = Device.objects.create(user=user)

        revoke_device(device, reason="logout")

        device.refresh_from_db()
        assert device.is_active is False
        assert device.revoked_reason == "logout"

    def test_revokes_every_active_refresh_token_for_the_device(self, user: AbstractUser) -> None:
        device = Device.objects.create(user=user)
        active = RefreshToken.objects.create(
            device=device, expires_at=timezone.now() + dt.timedelta(days=1)
        )
        already_revoked = RefreshToken.objects.create(
            device=device,
            expires_at=timezone.now() + dt.timedelta(days=1),
            revoked_at=timezone.now() - dt.timedelta(hours=1),
            revoked_reason="rotated",
        )

        revoke_device(device, reason="logout")

        active.refresh_from_db()
        already_revoked.refresh_from_db()
        assert active.revoked_reason == "logout"
        # An already-rotated token keeps its original reason; revoke_device
        # should not overwrite history that predates this call.
        assert already_revoked.revoked_reason == "rotated"

    def test_is_idempotent(self, user: AbstractUser) -> None:
        device = Device.objects.create(user=user)

        revoke_device(device, reason="logout")
        first_revoked_at = device.revoked_at

        revoke_device(device, reason="logout_all")
        device.refresh_from_db()

        assert device.revoked_at == first_revoked_at
        assert device.revoked_reason == "logout"


class TestRevokeAllDevices:
    def test_revokes_every_device(self, user: AbstractUser) -> None:
        first = Device.objects.create(user=user)
        second = Device.objects.create(user=user)

        revoked_count = revoke_all_devices(user, reason="logout_all")

        first.refresh_from_db()
        second.refresh_from_db()
        assert revoked_count == 2
        assert first.is_active is False
        assert second.is_active is False

    def test_leaves_the_excepted_device_active(self, user: AbstractUser) -> None:
        keep = Device.objects.create(user=user)
        other = Device.objects.create(user=user)

        revoke_all_devices(user, reason="logout_all", except_device=keep)

        keep.refresh_from_db()
        other.refresh_from_db()
        assert keep.is_active is True
        assert other.is_active is False

    def test_does_not_touch_other_users_devices(
        self, user: AbstractUser, other_user: AbstractUser
    ) -> None:
        mine = Device.objects.create(user=user)
        theirs = Device.objects.create(user=other_user)

        revoke_all_devices(user, reason="logout_all")

        mine.refresh_from_db()
        theirs.refresh_from_db()
        assert mine.is_active is False
        assert theirs.is_active is True

    def test_already_revoked_devices_are_not_counted_again(self, user: AbstractUser) -> None:
        Device.objects.create(user=user, revoked_at=timezone.now(), revoked_reason="logout")

        revoked_count = revoke_all_devices(user, reason="logout_all")

        assert revoked_count == 0
