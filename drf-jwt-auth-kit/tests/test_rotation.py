"""Tests for :mod:`drf_jwt_auth_kit.rotation`."""

from __future__ import annotations

import datetime as dt
import uuid

import pytest
from django.contrib.auth.models import AbstractUser
from django.test import override_settings
from django.utils import timezone
from freezegun import freeze_time

from drf_jwt_auth_kit.constants import CLAIM_JTI, CLAIM_USER_ID
from drf_jwt_auth_kit.exceptions import (
    DeviceRevokedError,
    InvalidTokenError,
    TokenReuseDetectedError,
)
from drf_jwt_auth_kit.models import Device, RefreshToken
from drf_jwt_auth_kit.rotation import issue_token_pair, rotate_refresh_token
from drf_jwt_auth_kit.tokens import decode_token, encode_refresh_token

pytestmark = pytest.mark.django_db


class TestIssueTokenPair:
    def test_creates_a_refresh_token_row(self, user: AbstractUser, device: Device) -> None:
        pair = issue_token_pair(user=user, device=device)

        claims = decode_token(pair.refresh_token, expected_type="refresh")
        assert RefreshToken.objects.filter(jti=claims[CLAIM_JTI], device=device).exists()

    def test_access_token_carries_the_user_id(self, user: AbstractUser, device: Device) -> None:
        pair = issue_token_pair(user=user, device=device)

        claims = decode_token(pair.access_token, expected_type="access")
        assert claims[CLAIM_USER_ID] == user.pk

    def test_remember_me_uses_the_longer_lifetime(self, user: AbstractUser, device: Device) -> None:
        pair = issue_token_pair(user=user, device=device, remember_me=True)

        claims = decode_token(pair.refresh_token, expected_type="refresh")
        row = RefreshToken.objects.get(jti=claims[CLAIM_JTI])
        assert row.remember_me is True


class TestRotateRefreshToken:
    def test_rotation_issues_a_new_token_and_revokes_the_old_one(
        self, user: AbstractUser, device: Device
    ) -> None:
        first_pair = issue_token_pair(user=user, device=device)
        first_claims = decode_token(first_pair.refresh_token, expected_type="refresh")

        second_pair = rotate_refresh_token(first_pair.refresh_token)
        second_claims = decode_token(second_pair.refresh_token, expected_type="refresh")

        assert second_claims[CLAIM_JTI] != first_claims[CLAIM_JTI]

        old_row = RefreshToken.objects.get(jti=first_claims[CLAIM_JTI])
        assert old_row.is_active is False
        assert old_row.revoked_reason == "rotated"
        assert str(old_row.replaced_by_id) == second_claims[CLAIM_JTI]

    def test_rotation_updates_device_last_used_at(self, user: AbstractUser, device: Device) -> None:
        pair = issue_token_pair(user=user, device=device)
        original_last_used = device.last_used_at

        # A small relative offset, not a fixed future date - jumping to an
        # arbitrary absolute time could land past the refresh token's own
        # (much shorter) expiry and fail for an unrelated reason.
        later = timezone.now() + dt.timedelta(seconds=5)
        with freeze_time(later):
            rotate_refresh_token(pair.refresh_token)

        device.refresh_from_db()
        assert device.last_used_at > original_last_used

    def test_reuse_of_a_rotated_token_is_detected(self, user: AbstractUser, device: Device) -> None:
        first_pair = issue_token_pair(user=user, device=device)
        rotate_refresh_token(first_pair.refresh_token)  # legitimate rotation

        with pytest.raises(TokenReuseDetectedError):
            rotate_refresh_token(first_pair.refresh_token)  # replay of the old token

    def test_reuse_detection_revokes_the_entire_device(
        self, user: AbstractUser, device: Device
    ) -> None:
        first_pair = issue_token_pair(user=user, device=device)
        second_pair = rotate_refresh_token(first_pair.refresh_token)

        with pytest.raises(TokenReuseDetectedError):
            rotate_refresh_token(first_pair.refresh_token)

        device.refresh_from_db()
        assert device.is_active is False
        assert device.revoked_reason == "reuse_detected"

        # Even the legitimately-rotated second token is now dead, since
        # the whole device was revoked - this is intentional: we cannot
        # tell which of the two parties holding a copy is the attacker.
        with pytest.raises(DeviceRevokedError):
            rotate_refresh_token(second_pair.refresh_token)

    def test_unknown_jti_raises_invalid_token(self, user: AbstractUser, device: Device) -> None:
        fake_token = encode_refresh_token(
            user_id=user.pk, device_id=device.pk, jti=uuid.uuid4(), lifetime=dt.timedelta(days=1)
        )

        with pytest.raises(InvalidTokenError):
            rotate_refresh_token(fake_token)

    def test_revoked_device_rejects_refresh_even_with_an_unused_token(
        self, user: AbstractUser, device: Device
    ) -> None:
        pair = issue_token_pair(user=user, device=device)
        device.revoked_at = timezone.now()
        device.revoked_reason = "logout"
        device.save(update_fields=["revoked_at", "revoked_reason"])

        with pytest.raises(DeviceRevokedError):
            rotate_refresh_token(pair.refresh_token)

    def test_remember_me_flag_survives_rotation(self, user: AbstractUser, device: Device) -> None:
        pair = issue_token_pair(user=user, device=device, remember_me=True)

        new_pair = rotate_refresh_token(pair.refresh_token)

        new_claims = decode_token(new_pair.refresh_token, expected_type="refresh")
        row = RefreshToken.objects.get(jti=new_claims[CLAIM_JTI])
        assert row.remember_me is True

    def test_blacklist_after_rotation_disabled_allows_repeated_use(
        self, user: AbstractUser, device: Device
    ) -> None:
        with override_settings(JWT_AUTH_KIT={"BLACKLIST_AFTER_ROTATION": False}):
            pair = issue_token_pair(user=user, device=device)
            rotate_refresh_token(pair.refresh_token)
            # No exception: the same (never-blacklisted) token can be used again.
            rotate_refresh_token(pair.refresh_token)
