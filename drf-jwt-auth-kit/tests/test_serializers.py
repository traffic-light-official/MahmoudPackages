"""Tests for :mod:`drf_jwt_auth_kit.serializers`."""

from __future__ import annotations

import pytest
from django.contrib.auth.models import AbstractUser

from drf_jwt_auth_kit.models import Device, LoginHistory
from drf_jwt_auth_kit.serializers import (
    DeviceSerializer,
    LoginHistorySerializer,
    LoginSerializer,
    TOTPConfirmSerializer,
    TOTPSetupResponseSerializer,
)

pytestmark = pytest.mark.django_db


class TestLoginSerializer:
    def test_requires_username_and_password(self) -> None:
        serializer = LoginSerializer(data={})

        assert serializer.is_valid() is False
        assert "username" in serializer.errors
        assert "password" in serializer.errors

    def test_optional_fields_default(self) -> None:
        serializer = LoginSerializer(data={"username": "ada", "password": "secret"})
        serializer.is_valid(raise_exception=True)

        assert serializer.validated_data["mfa_code"] == ""
        assert serializer.validated_data["remember_me"] is False
        assert serializer.validated_data["device_label"] == ""


class TestDeviceSerializer:
    def test_marks_the_current_device(self, user: AbstractUser) -> None:
        device = Device.objects.create(user=user, label="Laptop")

        data = DeviceSerializer(device, context={"current_device_id": device.pk}).data

        assert data["is_current"] is True

    def test_marks_other_devices_as_not_current(self, user: AbstractUser) -> None:
        device = Device.objects.create(user=user, label="Laptop")
        other = Device.objects.create(user=user, label="Phone")

        data = DeviceSerializer(other, context={"current_device_id": device.pk}).data

        assert data["is_current"] is False

    def test_defaults_to_not_current_without_context(self, user: AbstractUser) -> None:
        device = Device.objects.create(user=user)

        data = DeviceSerializer(device).data

        assert data["is_current"] is False

    def test_fields_are_read_only(self) -> None:
        serializer = DeviceSerializer(data={"label": "hack"})
        serializer.is_valid(raise_exception=True)

        assert serializer.validated_data == {}


class TestLoginHistorySerializer:
    def test_serializes_expected_fields(self, user: AbstractUser) -> None:
        entry = LoginHistory.objects.create(user=user, username_attempted="ada", success=True)

        data = LoginHistorySerializer(entry).data

        assert data["username_attempted"] == "ada"
        assert data["success"] is True


class TestTOTPSerializers:
    def test_setup_response_serializes_a_plain_dict(self) -> None:
        data = TOTPSetupResponseSerializer(
            {"secret": "ABC123", "provisioning_uri": "otpauth://totp/x"}
        ).data

        assert data["secret"] == "ABC123"
        assert data["provisioning_uri"] == "otpauth://totp/x"

    def test_confirm_requires_code(self) -> None:
        serializer = TOTPConfirmSerializer(data={})

        assert serializer.is_valid() is False
        assert "code" in serializer.errors
