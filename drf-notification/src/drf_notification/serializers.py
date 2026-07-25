"""DRF serializers for the notification preference center."""

from __future__ import annotations

from rest_framework import serializers

from drf_notification.models import (
    Notification,
    NotificationPreference,
    NotificationSettings,
    WebhookTarget,
)
from drf_notification.url_safety import UnsafeWebhookUrlError, validate_public_url


class NotificationSerializer(serializers.ModelSerializer[Notification]):
    """Read-only representation of a single delivered/queued notification."""

    is_read = serializers.BooleanField(read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "event_key",
            "channel",
            "subject",
            "body",
            "status",
            "created_at",
            "sent_at",
            "read_at",
            "is_read",
        ]
        read_only_fields = fields


class NotificationPreferenceSerializer(serializers.ModelSerializer[NotificationPreference]):
    """Create/update a single per-event-type, per-channel opt-in/opt-out row."""

    class Meta:
        model = NotificationPreference
        fields = ["id", "event_key", "channel", "enabled"]
        read_only_fields = ["id"]


class NotificationSettingsSerializer(serializers.ModelSerializer[NotificationSettings]):
    """The authenticated user's digest frequency, quiet hours, and global opt-out."""

    class Meta:
        model = NotificationSettings
        fields = [
            "digest_frequency",
            "quiet_hours_start",
            "quiet_hours_end",
            "timezone_name",
            "unsubscribed_all",
        ]


class WebhookTargetSerializer(serializers.ModelSerializer[WebhookTarget]):
    """Create/update a webhook target, rejecting obviously unsafe URLs."""

    class Meta:
        model = WebhookTarget
        fields = ["id", "url", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_url(self, value: str) -> str:
        try:
            validate_public_url(value)
        except UnsafeWebhookUrlError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        return value
