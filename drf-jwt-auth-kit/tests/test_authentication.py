"""Tests for :mod:`drf_jwt_auth_kit.authentication`."""

from __future__ import annotations

import datetime as dt
import uuid

import pytest
from django.contrib.auth.models import AbstractUser
from django.test import override_settings
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIRequestFactory

from drf_jwt_auth_kit.authentication import JWTAuthentication
from drf_jwt_auth_kit.models import Device
from drf_jwt_auth_kit.tokens import encode_access_token, encode_refresh_token

pytestmark = pytest.mark.django_db


class TestAuthenticate:
    def test_returns_none_without_an_authorization_header(self, api_rf: APIRequestFactory) -> None:
        request = api_rf.get("/")

        assert JWTAuthentication().authenticate(request) is None

    def test_returns_none_for_a_non_bearer_scheme(self, api_rf: APIRequestFactory) -> None:
        request = api_rf.get("/", HTTP_AUTHORIZATION="Basic dXNlcjpwYXNz")

        assert JWTAuthentication().authenticate(request) is None

    def test_authenticates_a_valid_access_token(
        self, user: AbstractUser, device: Device, api_rf: APIRequestFactory
    ) -> None:
        token = encode_access_token(user_id=user.pk, device_id=device.pk)
        request = api_rf.get("/", HTTP_AUTHORIZATION=f"Bearer {token}")

        result = JWTAuthentication().authenticate(request)

        assert result is not None
        authenticated_user, claims = result
        assert authenticated_user.pk == user.pk
        assert claims["user_id"] == user.pk

    def test_rejects_a_malformed_authorization_header(self, api_rf: APIRequestFactory) -> None:
        request = api_rf.get("/", HTTP_AUTHORIZATION="Bearer")

        with pytest.raises(AuthenticationFailed, match="Malformed"):
            JWTAuthentication().authenticate(request)

    def test_rejects_an_expired_token(
        self, user: AbstractUser, device: Device, api_rf: APIRequestFactory
    ) -> None:
        with override_settings(JWT_AUTH_KIT={"ACCESS_TOKEN_LIFETIME": dt.timedelta(seconds=-1)}):
            token = encode_access_token(user_id=user.pk, device_id=device.pk)
        request = api_rf.get("/", HTTP_AUTHORIZATION=f"Bearer {token}")

        with pytest.raises(AuthenticationFailed, match="expired"):
            JWTAuthentication().authenticate(request)

    def test_rejects_a_refresh_token_presented_as_access(
        self, user: AbstractUser, device: Device, api_rf: APIRequestFactory
    ) -> None:
        token = encode_refresh_token(
            user_id=user.pk, device_id=device.pk, jti=uuid.uuid4(), lifetime=dt.timedelta(days=1)
        )
        request = api_rf.get("/", HTTP_AUTHORIZATION=f"Bearer {token}")

        with pytest.raises(AuthenticationFailed, match="Invalid"):
            JWTAuthentication().authenticate(request)

    def test_rejects_unknown_user(self, device: Device, api_rf: APIRequestFactory) -> None:
        token = encode_access_token(user_id=999999, device_id=device.pk)
        request = api_rf.get("/", HTTP_AUTHORIZATION=f"Bearer {token}")

        with pytest.raises(AuthenticationFailed, match="not found"):
            JWTAuthentication().authenticate(request)

    def test_rejects_inactive_user(
        self, user: AbstractUser, device: Device, api_rf: APIRequestFactory
    ) -> None:
        user.is_active = False
        user.save(update_fields=["is_active"])
        token = encode_access_token(user_id=user.pk, device_id=device.pk)
        request = api_rf.get("/", HTTP_AUTHORIZATION=f"Bearer {token}")

        with pytest.raises(AuthenticationFailed, match="inactive"):
            JWTAuthentication().authenticate(request)

    def test_device_revocation_check_disabled_by_default(
        self, user: AbstractUser, device: Device, api_rf: APIRequestFactory
    ) -> None:
        device.revoked_at = timezone.now()
        device.revoked_reason = "logout"
        device.save(update_fields=["revoked_at", "revoked_reason"])
        token = encode_access_token(user_id=user.pk, device_id=device.pk)
        request = api_rf.get("/", HTTP_AUTHORIZATION=f"Bearer {token}")

        result = JWTAuthentication().authenticate(request)

        assert result is not None

    def test_device_revocation_check_when_enabled(
        self, user: AbstractUser, device: Device, api_rf: APIRequestFactory
    ) -> None:
        device.revoked_at = timezone.now()
        device.revoked_reason = "logout"
        device.save(update_fields=["revoked_at", "revoked_reason"])
        token = encode_access_token(user_id=user.pk, device_id=device.pk)
        request = api_rf.get("/", HTTP_AUTHORIZATION=f"Bearer {token}")

        with (
            override_settings(JWT_AUTH_KIT={"CHECK_DEVICE_REVOCATION_ON_AUTH": True}),
            pytest.raises(AuthenticationFailed, match="logged out"),
        ):
            JWTAuthentication().authenticate(request)


class TestAuthenticateHeader:
    def test_returns_bearer_realm(self, api_rf: APIRequestFactory) -> None:
        header = JWTAuthentication().authenticate_header(api_rf.get("/"))

        assert header == 'Bearer realm="api"'
