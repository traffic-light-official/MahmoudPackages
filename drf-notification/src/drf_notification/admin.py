"""Django admin registration for :mod:`drf_notification` models."""

from __future__ import annotations

from django.contrib import admin
from django.http import HttpRequest

from drf_notification.models import (
    Notification,
    NotificationPreference,
    NotificationSettings,
    NotificationTemplate,
    WebhookTarget,
)


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("user", "digest_frequency", "unsubscribed_all", "timezone_name")
    list_filter = ("digest_frequency", "unsubscribed_all")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("unsubscribe_token", "created_at", "updated_at")


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("user", "event_key", "channel", "enabled")
    list_filter = ("channel", "enabled")
    search_fields = ("user__username", "user__email", "event_key")


@admin.register(WebhookTarget)
class WebhookTargetAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("user", "url", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("user__username", "url")
    readonly_fields = ("secret", "created_at")


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("event_key", "channel", "language", "updated_at")
    list_filter = ("channel", "language")
    search_fields = ("event_key",)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("recipient", "event_key", "channel", "status", "created_at", "sent_at")
    list_filter = ("channel", "status")
    search_fields = ("recipient__username", "event_key", "subject")
    readonly_fields = ("created_at", "sent_at", "read_at")

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def get_readonly_fields(
        self, request: HttpRequest, obj: Notification | None = None
    ) -> tuple[str, ...] | list[str]:
        del request, obj
        return [field.name for field in Notification._meta.fields]
