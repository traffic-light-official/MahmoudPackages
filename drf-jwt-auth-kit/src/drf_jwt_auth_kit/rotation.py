"""Issues and rotates access/refresh token pairs, with reuse detection."""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING, NamedTuple

from django.db.models import Model
from django.utils import timezone

from drf_jwt_auth_kit.constants import (
    CLAIM_JTI,
    REVOKED_REASON_REUSE_DETECTED,
    REVOKED_REASON_ROTATED,
    TOKEN_TYPE_REFRESH,
)
from drf_jwt_auth_kit.devices import revoke_device, touch_device
from drf_jwt_auth_kit.exceptions import (
    DeviceRevokedError,
    InvalidTokenError,
    TokenReuseDetectedError,
)
from drf_jwt_auth_kit.models import Device, RefreshToken
from drf_jwt_auth_kit.settings import get_setting
from drf_jwt_auth_kit.tokens import decode_token, encode_access_token, encode_refresh_token

if TYPE_CHECKING:
    import uuid


class TokenPair(NamedTuple):
    """An issued access/refresh token pair and the device they belong to."""

    access_token: str
    refresh_token: str
    device: Device


def _lifetime_for(*, remember_me: bool) -> dt.timedelta:
    key = "REMEMBER_ME_REFRESH_TOKEN_LIFETIME" if remember_me else "REFRESH_TOKEN_LIFETIME"
    result: dt.timedelta = get_setting(key)
    return result


def issue_token_pair(*, user: Model, device: Device, remember_me: bool = False) -> TokenPair:
    """Issue a brand-new access/refresh token pair for an already-created device.

    Args:
        user: The authenticated user.
        device: The device (session) these tokens belong to - typically
            just created by :func:`~drf_jwt_auth_kit.devices.create_device`.
        remember_me: Whether to use ``REMEMBER_ME_REFRESH_TOKEN_LIFETIME``
            instead of the normal, shorter ``REFRESH_TOKEN_LIFETIME``.

    Returns:
        The new access token, refresh token, and the device they belong to.
    """
    lifetime = _lifetime_for(remember_me=remember_me)
    refresh_row = RefreshToken.objects.create(
        device=device, expires_at=timezone.now() + lifetime, remember_me=remember_me
    )
    access_token = encode_access_token(user_id=user.pk, device_id=device.pk)
    refresh_token = encode_refresh_token(
        user_id=user.pk, device_id=device.pk, jti=refresh_row.jti, lifetime=lifetime
    )
    return TokenPair(access_token=access_token, refresh_token=refresh_token, device=device)


def rotate_refresh_token(raw_refresh_token: str) -> TokenPair:
    """Verify, rotate, and reissue a refresh token.

    Args:
        raw_refresh_token: The raw JWT refresh token (typically read from
            the httpOnly refresh cookie).

    Returns:
        A new token pair for the same device.

    Raises:
        InvalidTokenError: If the token is malformed, has the wrong
            type, or its ``jti`` does not correspond to a known row.
        TokenExpiredError: If the token has expired.
        TokenReuseDetectedError: If this token was already rotated away
            - every refresh token for the device has already been
            revoked by the time this is raised.
        DeviceRevokedError: If the device itself was revoked (e.g. via
            logout-all) independent of this specific token.
    """
    claims = decode_token(raw_refresh_token, expected_type=TOKEN_TYPE_REFRESH)
    jti: uuid.UUID = claims[CLAIM_JTI]

    try:
        old_token = RefreshToken.objects.select_related("device").get(jti=jti)
    except RefreshToken.DoesNotExist as exc:
        raise InvalidTokenError("Refresh token does not correspond to a known session.") from exc

    device = old_token.device

    if not device.is_active:
        raise DeviceRevokedError("This device has been logged out.")

    blacklist_after_rotation = get_setting("BLACKLIST_AFTER_ROTATION")

    if blacklist_after_rotation and not old_token.is_active:
        # Reuse: this exact token was already rotated away (or revoked),
        # yet it's being presented again. Revoke the whole device - the
        # legitimate client's own refresh token becomes void too, forcing
        # a fresh login, but that is strictly safer than letting a
        # potentially-stolen token keep working.
        revoke_device(device, reason=REVOKED_REASON_REUSE_DETECTED)
        raise TokenReuseDetectedError(
            "This refresh token has already been used. "
            "The associated device has been logged out."
        )

    if blacklist_after_rotation:
        old_token.revoked_at = timezone.now()
        old_token.revoked_reason = REVOKED_REASON_ROTATED
        old_token.save(update_fields=["revoked_at", "revoked_reason"])

    lifetime = _lifetime_for(remember_me=old_token.remember_me)
    new_token_row = RefreshToken.objects.create(
        device=device, expires_at=timezone.now() + lifetime, remember_me=old_token.remember_me
    )
    if blacklist_after_rotation:
        old_token.replaced_by = new_token_row
        old_token.save(update_fields=["replaced_by"])

    touch_device(device)

    access_token = encode_access_token(user_id=device.user_id, device_id=device.pk)
    refresh_token = encode_refresh_token(
        user_id=device.user_id,
        device_id=device.pk,
        jti=new_token_row.jti,
        lifetime=lifetime,
    )
    return TokenPair(access_token=access_token, refresh_token=refresh_token, device=device)
