"""Smoke tests for Django admin registration in :mod:`drf_notification.admin`."""

from __future__ import annotations

import pytest
from django.contrib import admin
from django.contrib.admin.sites import AdminSite

from drf_notification.admin import NotificationAdmin
from drf_notification.models import (
    Notification,
    NotificationPreference,
    NotificationSettings,
    NotificationTemplate,
    WebhookTarget,
)

pytestmark = pytest.mark.django_db


class TestAdminRegistration:
    @pytest.mark.parametrize(
        "model",
        [
            Notification,
            NotificationPreference,
            NotificationSettings,
            NotificationTemplate,
            WebhookTarget,
        ],
    )
    def test_model_is_registered(self, model: type) -> None:
        assert model in admin.site._registry


class TestNotificationAdmin:
    def test_has_no_add_permission(self) -> None:
        model_admin = NotificationAdmin(Notification, AdminSite())

        assert model_admin.has_add_permission(request=None) is False  # type: ignore[arg-type]

    def test_every_field_is_read_only(self) -> None:
        model_admin = NotificationAdmin(Notification, AdminSite())

        readonly = model_admin.get_readonly_fields(request=None, obj=None)  # type: ignore[arg-type]

        assert "event_key" in readonly
        assert "status" in readonly
