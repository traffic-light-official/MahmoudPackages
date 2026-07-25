"""Database models backing :mod:`drf_notification`.

Event *types* are a code-level registry (see :mod:`drf_notification.events`);
everything here is per-user state (preferences, settings, webhook targets)
or a delivery record (:class:`Notification`, :class:`NotificationTemplate`).
"""

from __future__ import annotations

import secrets
from typing import Any

from django.conf import settings
from django.db import models
from django.utils import timezone

from drf_notification.constants import (
    CHANNEL_CHOICES,
    DIGEST_FREQUENCY_CHOICES,
    STATUS_CHOICES,
    STATUS_PENDING,
)
from drf_notification.settings import get_setting


def _generate_unsubscribe_token() -> str:
    return secrets.token_urlsafe(32)


def _generate_webhook_secret() -> str:
    return secrets.token_hex(32)


def _default_digest_frequency() -> str:
    result: str = get_setting("DEFAULT_DIGEST_FREQUENCY")
    return result


class NotificationSettings(models.Model):
    """Per-user delivery preferences that apply across every event type."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_settings"
    )
    digest_frequency = models.CharField(
        max_length=16, choices=DIGEST_FREQUENCY_CHOICES, default=_default_digest_frequency
    )
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    timezone_name = models.CharField(
        max_length=64,
        blank=True,
        help_text=(
            "IANA timezone name, e.g. 'America/New_York'. Empty uses the project's TIME_ZONE."
        ),
    )
    unsubscribed_all = models.BooleanField(default=False)
    unsubscribe_token = models.CharField(
        max_length=64, unique=True, editable=False, default=_generate_unsubscribe_token
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "notification settings"
        verbose_name_plural = "notification settings"

    def __str__(self) -> str:
        return f"NotificationSettings(user_id={self.user_id})"

    def has_quiet_hours(self) -> bool:
        """Return whether both ends of a quiet-hours window are configured."""
        return self.quiet_hours_start is not None and self.quiet_hours_end is not None


class NotificationPreference(models.Model):
    """Per-user, per-event-type, per-channel opt-in/opt-out state."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_preferences"
    )
    event_key = models.CharField(max_length=100)
    channel = models.CharField(max_length=16, choices=CHANNEL_CHOICES)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "event_key", "channel"], name="unique_user_event_channel_preference"
            )
        ]
        indexes = [models.Index(fields=["user", "event_key"])]

    def __str__(self) -> str:
        state = "enabled" if self.enabled else "disabled"
        return f"{self.event_key}/{self.channel} ({state}) for user_id={self.user_id}"


class WebhookTarget(models.Model):
    """A user-registered webhook endpoint for the ``webhook`` channel."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="webhook_targets"
    )
    url = models.URLField()
    secret = models.CharField(max_length=64, editable=False, default=_generate_webhook_secret)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"WebhookTarget(user_id={self.user_id}, url={self.url})"


class NotificationTemplate(models.Model):
    """An admin-editable subject/body template for one event type, channel, and language.

    Rendered with :mod:`django.template` using the notification's
    ``context``. If no row exists for a given ``(event_key, channel,
    language)``, :mod:`drf_notification.rendering` falls back to a plain,
    unstyled default derived from the event's description.
    """

    event_key = models.CharField(max_length=100)
    channel = models.CharField(max_length=16, choices=CHANNEL_CHOICES)
    language = models.CharField(max_length=10, default="en")
    subject_template = models.TextField(
        blank=True, help_text="Django template syntax. Unused for channels with no subject line."
    )
    body_template = models.TextField(help_text="Django template syntax.")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event_key", "channel", "language"], name="unique_event_channel_language"
            )
        ]

    def __str__(self) -> str:
        return f"{self.event_key}/{self.channel}/{self.language}"


class Notification(models.Model):
    """A single delivery record: one attempt to notify one user on one channel."""

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    event_key = models.CharField(max_length=100)
    channel = models.CharField(max_length=16, choices=CHANNEL_CHOICES)
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField(blank=True)
    context = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    attempts = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        # "-id" breaks ties deterministically when two rows share the same
        # created_at value (auto_now_add resolution, or a burst of inserts
        # within one notify() call) - without it, ties fall back to
        # unspecified database order.
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["recipient", "channel", "status"]),
            models.Index(fields=["recipient", "event_key"]),
        ]

    def __str__(self) -> str:
        return f"Notification({self.event_key}/{self.channel} -> user_id={self.recipient_id})"

    @property
    def is_read(self) -> bool:
        """Whether this notification has been marked read (relevant to ``in_app`` only)."""
        return self.read_at is not None

    def mark_read(self) -> None:
        """Mark this notification as read, if it isn't already, and persist the change."""
        if self.read_at is None:
            self.read_at = timezone.now()
            self.save(update_fields=["read_at"])

    def mark_sent(self) -> None:
        """Mark this notification as successfully delivered and persist the change."""
        self.status = "sent"
        self.sent_at = timezone.now()
        self.save(update_fields=["status", "sent_at"])

    def mark_failed(self, error: str) -> None:
        """Record a failed delivery attempt and persist the change.

        Args:
            error: A short description of what went wrong, stored in
                ``last_error`` (never the raw exception traceback).
        """
        self.attempts += 1
        self.last_error = error
        self.status = "failed"
        self.save(update_fields=["attempts", "last_error", "status"])

    def to_context_dict(self) -> dict[str, Any]:
        """Return ``context`` merged with a few always-available template variables."""
        return {**self.context, "event_key": self.event_key, "subject": self.subject}
