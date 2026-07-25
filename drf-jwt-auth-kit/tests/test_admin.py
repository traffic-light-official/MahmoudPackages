"""Smoke tests for Django admin registration in :mod:`drf_jwt_auth_kit.admin`."""

from __future__ import annotations

import pytest
from django.contrib import admin
from django.contrib.admin.sites import AdminSite

from drf_jwt_auth_kit.admin import DeviceAdmin, RefreshTokenAdmin
from drf_jwt_auth_kit.models import Device, LoginHistory, RefreshToken, TOTPDevice

pytestmark = pytest.mark.django_db


class TestAdminRegistration:
    @pytest.mark.parametrize("model", [Device, RefreshToken, LoginHistory, TOTPDevice])
    def test_model_is_registered(self, model: type) -> None:
        assert model in admin.site._registry


class TestDeviceAdmin:
    def test_is_active_reflects_revocation(self, user: object) -> None:
        device = Device.objects.create(user=user)
        model_admin = DeviceAdmin(Device, AdminSite())

        assert model_admin.is_active(device) is True


class TestRefreshTokenAdmin:
    def test_has_no_add_permission(self) -> None:
        model_admin = RefreshTokenAdmin(RefreshToken, AdminSite())

        assert model_admin.has_add_permission(request=None) is False  # type: ignore[arg-type]
