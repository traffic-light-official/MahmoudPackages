"""Database models backing :mod:`drf_jwt_auth_kit`.

A :class:`Device` doubles as this package's session record: every login
creates one, every refresh reuses the same one (only the
:class:`RefreshToken` rotates), and "log out everywhere" means revoking
every :class:`Device` a user has.
"""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

from drf_jwt_auth_kit.constants import LOGIN_FAILURE_CHOICES, REVOKED_REASON_CHOICES


class Device(models.Model):
    """One logged-in session/device for a user.

    Created at login, updated (``last_used_at``) on every successful
    refresh, and revoked on logout (this device) or logout-all (every
    device). Revoking a device also revokes every
    :class:`RefreshToken` that belongs to it.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="auth_kit_devices"
    )
    label = models.CharField(
        max_length=255,
        blank=True,
        help_text="Client-supplied display name, e.g. 'iPhone 15' or 'Chrome on macOS'.",
    )
    user_agent = models.CharField(max_length=512, blank=True)
    created_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_reason = models.CharField(max_length=20, choices=REVOKED_REASON_CHOICES, blank=True)

    class Meta:
        ordering = ["-last_used_at", "-id"]
        indexes = [models.Index(fields=["user", "revoked_at"])]

    def __str__(self) -> str:
        return self.label or f"Device({self.id})"

    @property
    def is_active(self) -> bool:
        """Whether this device has not been revoked."""
        return self.revoked_at is None


class RefreshToken(models.Model):
    """One issued refresh token, tracked for rotation and reuse detection."""

    jti = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="refresh_tokens")
    issued_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    remember_me = models.BooleanField(default=False)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_reason = models.CharField(max_length=20, choices=REVOKED_REASON_CHOICES, blank=True)
    replaced_by = models.OneToOneField(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="replaces",
    )

    class Meta:
        indexes = [models.Index(fields=["device", "revoked_at"])]

    def __str__(self) -> str:
        return f"RefreshToken({self.jti})"

    @property
    def is_active(self) -> bool:
        """Whether this token has not been revoked (rotated away or otherwise)."""
        return self.revoked_at is None


class LoginHistory(models.Model):
    """A record of one login attempt, successful or not."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="auth_kit_login_history",
    )
    username_attempted = models.CharField(max_length=255)
    device = models.ForeignKey(
        Device, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    success = models.BooleanField(default=False)
    failure_reason = models.CharField(max_length=30, choices=LOGIN_FAILURE_CHOICES, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "login history"
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["user", "created_at"])]

    def __str__(self) -> str:
        outcome = "success" if self.success else f"failed ({self.failure_reason})"
        return f"LoginHistory({self.username_attempted}, {outcome})"


class TOTPDevice(models.Model):
    """A user's TOTP (RFC 6238) secret, used by :class:`~drf_jwt_auth_kit.mfa.TOTPProvider`."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="auth_kit_totp_device"
    )
    secret = models.CharField(max_length=64, help_text="Base32-encoded TOTP shared secret.")
    confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        state = "confirmed" if self.confirmed else "pending"
        return f"TOTPDevice(user_id={self.user_id}, {state})"
