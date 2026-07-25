"""Django admin registration for :mod:`drf_jwt_auth_kit` models."""

from __future__ import annotations

from django.contrib import admin
from django.http import HttpRequest

from drf_jwt_auth_kit.models import Device, LoginHistory, RefreshToken, TOTPDevice


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("id", "user", "label", "created_at", "last_used_at", "is_active")
    list_filter = ("revoked_reason",)
    search_fields = ("user__username", "label", "user_agent")
    readonly_fields = ("id", "created_at", "last_used_at")

    @admin.display(boolean=True)
    def is_active(self, device: Device) -> bool:
        return device.is_active


@admin.register(RefreshToken)
class RefreshTokenAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("jti", "device", "issued_at", "expires_at", "remember_me", "is_active")
    list_filter = ("revoked_reason", "remember_me")
    readonly_fields = ("jti", "issued_at")

    @admin.display(boolean=True)
    def is_active(self, refresh_token: RefreshToken) -> bool:
        return refresh_token.is_active

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("username_attempted", "user", "success", "failure_reason", "created_at")
    list_filter = ("success", "failure_reason")
    search_fields = ("username_attempted", "user__username", "ip_address")

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False


@admin.register(TOTPDevice)
class TOTPDeviceAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("user", "confirmed", "created_at", "confirmed_at")
    list_filter = ("confirmed",)
    readonly_fields = ("secret", "created_at")
