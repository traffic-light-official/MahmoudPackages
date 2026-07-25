"""DRF authentication class reading JWT access tokens from the ``Authorization`` header."""

from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.utils.translation import gettext_lazy as _
from rest_framework import authentication, exceptions

from drf_jwt_auth_kit.constants import (
    AUTH_HEADER_PREFIX,
    CLAIM_DEVICE_ID,
    CLAIM_USER_ID,
    TOKEN_TYPE_ACCESS,
)
from drf_jwt_auth_kit.exceptions import InvalidTokenError, TokenExpiredError
from drf_jwt_auth_kit.models import Device
from drf_jwt_auth_kit.settings import get_setting
from drf_jwt_auth_kit.tokens import decode_token


class JWTAuthentication(authentication.BaseAuthentication):
    """Authenticates requests bearing ``Authorization: Bearer <access token>``.

    Verification is stateless (no database query) unless the
    ``CHECK_DEVICE_REVOCATION_ON_AUTH`` setting is enabled, in which case
    one extra query confirms the token's device has not been revoked.
    """

    www_authenticate_realm = "api"

    def authenticate(self, request: Any) -> tuple[AbstractBaseUser, dict[str, Any]] | None:
        """Return ``(user, claims)`` for a valid Bearer access token, or ``None``.

        Args:
            request: The incoming DRF request.

        Returns:
            ``None`` if no ``Authorization: Bearer ...`` header is
            present (so other authentication classes get a chance), or
            the authenticated user and decoded claims.

        Raises:
            rest_framework.exceptions.AuthenticationFailed: If a Bearer
                token is present but invalid, expired, for an unknown or
                inactive user, or (with ``CHECK_DEVICE_REVOCATION_ON_AUTH``)
                for a revoked device.
        """
        header = self._get_header(request)
        if header is None:
            return None
        raw_token = self._get_raw_token(header)
        if raw_token is None:
            return None

        try:
            claims = decode_token(raw_token, expected_type=TOKEN_TYPE_ACCESS)
        except TokenExpiredError as exc:
            raise exceptions.AuthenticationFailed(
                _("Access token has expired."), code="token_expired"
            ) from exc
        except InvalidTokenError as exc:
            raise exceptions.AuthenticationFailed(
                _("Invalid access token."), code="token_invalid"
            ) from exc

        user = self._get_user(claims)

        if get_setting("CHECK_DEVICE_REVOCATION_ON_AUTH"):
            self._check_device_not_revoked(claims)

        return user, claims

    def authenticate_header(self, request: Any) -> str:
        """Return the ``WWW-Authenticate`` header value for a 401 response."""
        return f'{AUTH_HEADER_PREFIX} realm="{self.www_authenticate_realm}"'

    def _get_header(self, request: Any) -> str | None:
        header = request.META.get("HTTP_AUTHORIZATION")
        return header if isinstance(header, str) else None

    def _get_raw_token(self, header: str) -> str | None:
        parts = header.split()
        if not parts or parts[0] != AUTH_HEADER_PREFIX:
            return None
        if len(parts) != 2:
            raise exceptions.AuthenticationFailed(
                _("Malformed Authorization header."), code="bad_authorization_header"
            )
        return parts[1]

    def _get_user(self, claims: dict[str, Any]) -> AbstractBaseUser:
        user_model = get_user_model()
        try:
            user: AbstractBaseUser = user_model.objects.get(pk=claims[CLAIM_USER_ID])
        except user_model.DoesNotExist as exc:
            raise exceptions.AuthenticationFailed(
                _("User not found."), code="user_not_found"
            ) from exc
        if not user.is_active:
            raise exceptions.AuthenticationFailed(_("User is inactive."), code="user_inactive")
        return user

    def _check_device_not_revoked(self, claims: dict[str, Any]) -> None:
        device_id = claims.get(CLAIM_DEVICE_ID)
        if device_id is None:
            return
        is_active = Device.objects.filter(pk=device_id, revoked_at__isnull=True).exists()
        if not is_active:
            raise exceptions.AuthenticationFailed(
                _("Device has been logged out."), code="device_revoked"
            )
