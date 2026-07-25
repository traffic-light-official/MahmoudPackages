"""Device (session) lifecycle: creation, revocation, and "logout everywhere"."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db.models import Model
from django.utils import timezone

from drf_jwt_auth_kit.models import Device

if TYPE_CHECKING:
    from django.http import HttpRequest


def create_device(*, user: Model, request: HttpRequest | None, label: str = "") -> Device:
    """Create a new :class:`~drf_jwt_auth_kit.models.Device` for a login.

    Args:
        user: The user who just logged in.
        request: The current request, used to capture the client IP and
            user agent for display in the device list. Pass ``None`` if
            no request is available (e.g. a management command).
        label: Client-supplied display name, e.g. ``"iPhone 15"``.

    Returns:
        The newly created device.
    """
    user_agent = ""
    created_ip = None
    if request is not None:
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:512]
        created_ip = _client_ip(request)
    return Device.objects.create(  # type: ignore[misc]
        user=user, label=label, user_agent=user_agent, created_ip=created_ip
    )


def touch_device(device: Device) -> None:
    """Update a device's ``last_used_at`` timestamp to now.

    Args:
        device: The device to update.
    """
    device.last_used_at = timezone.now()
    device.save(update_fields=["last_used_at"])


def revoke_device(device: Device, *, reason: str) -> None:
    """Revoke a device and every refresh token that belongs to it.

    Args:
        device: The device to revoke.
        reason: One of the ``REVOKED_REASON_*`` constants.
    """
    now = timezone.now()
    if device.revoked_at is None:
        device.revoked_at = now
        device.revoked_reason = reason
        device.save(update_fields=["revoked_at", "revoked_reason"])
    device.refresh_tokens.filter(revoked_at__isnull=True).update(
        revoked_at=now, revoked_reason=reason
    )


def revoke_all_devices(user: Model, *, reason: str, except_device: Device | None = None) -> int:
    """Revoke every active device belonging to ``user``.

    Args:
        user: The user to log out everywhere.
        reason: One of the ``REVOKED_REASON_*`` constants.
        except_device: A device to leave untouched (e.g. the one making
            the "log out everywhere else" request).

    Returns:
        The number of devices revoked.
    """
    queryset = Device.objects.filter(user=user, revoked_at__isnull=True)  # type: ignore[misc]
    if except_device is not None:
        queryset = queryset.exclude(pk=except_device.pk)

    revoked = 0
    for device in queryset:
        revoke_device(device, reason=reason)
        revoked += 1
    return revoked


def _client_ip(request: HttpRequest) -> str | None:
    forwarded_for: str | None = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    remote_addr: str | None = request.META.get("REMOTE_ADDR")
    return remote_addr if remote_addr else None
