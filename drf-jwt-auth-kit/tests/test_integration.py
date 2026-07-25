"""End-to-end tests hitting the real URL-routed DRF API."""

from __future__ import annotations

import re

import pytest
from django.contrib.auth.models import AbstractUser
from rest_framework.test import APIClient

from drf_jwt_auth_kit.mfa import generate_totp_code, generate_totp_secret
from drf_jwt_auth_kit.models import Device, LoginHistory, RefreshToken, TOTPDevice

pytestmark = pytest.mark.django_db


def _login(
    client: APIClient, *, username: str = "ada", password: str = "s3cret-password", **extra: object
) -> object:
    return client.post(
        "/auth/login/", {"username": username, "password": password, **extra}, format="json"
    )


def _csrf_headers(client: APIClient) -> dict[str, str]:
    csrf_cookie = client.cookies.get("refresh_csrftoken")
    assert csrf_cookie is not None
    return {"HTTP_X_REFRESH_CSRFTOKEN": csrf_cookie.value}


class TestLogin:
    def test_valid_credentials_returns_access_token_and_sets_cookies(
        self, api_client: APIClient, user: AbstractUser
    ) -> None:
        response = _login(api_client)

        assert response.status_code == 200
        assert "access_token" in response.data
        assert "refresh_token" in response.cookies
        assert "refresh_csrftoken" in response.cookies
        assert response.cookies["refresh_token"]["httponly"] is True

    def test_invalid_password_is_rejected(self, api_client: APIClient, user: AbstractUser) -> None:
        response = _login(api_client, password="wrong-password")

        assert response.status_code == 401
        assert "refresh_token" not in response.cookies

    def test_unknown_username_is_rejected(self, api_client: APIClient) -> None:
        response = _login(api_client, username="nobody")

        assert response.status_code == 401

    def test_login_is_recorded_in_history(self, api_client: APIClient, user: AbstractUser) -> None:
        _login(api_client)
        _login(api_client, password="wrong-password")

        history = list(LoginHistory.objects.order_by("created_at"))
        assert history[0].success is True
        assert history[1].success is False
        assert history[1].failure_reason == "invalid_credentials"

    def test_login_creates_a_device(self, api_client: APIClient, user: AbstractUser) -> None:
        _login(api_client, device_label="My Test Browser")

        device = Device.objects.get(user=user)
        assert device.label == "My Test Browser"


class TestMfaLogin:
    def test_login_requires_mfa_code_once_enabled(
        self, api_client: APIClient, user: AbstractUser
    ) -> None:
        secret = generate_totp_secret()
        TOTPDevice.objects.create(user=user, secret=secret, confirmed=True)

        response = _login(api_client)

        assert response.status_code == 401
        assert response.data["mfa_required"] is True
        assert "refresh_token" not in response.cookies

    def test_login_succeeds_with_correct_mfa_code(
        self, api_client: APIClient, user: AbstractUser
    ) -> None:
        secret = generate_totp_secret()
        TOTPDevice.objects.create(user=user, secret=secret, confirmed=True)
        code = generate_totp_code(secret)

        response = _login(api_client, mfa_code=code)

        assert response.status_code == 200
        assert "access_token" in response.data

    def test_login_rejects_wrong_mfa_code(self, api_client: APIClient, user: AbstractUser) -> None:
        secret = generate_totp_secret()
        TOTPDevice.objects.create(user=user, secret=secret, confirmed=True)

        response = _login(api_client, mfa_code="000000")

        assert response.status_code == 401
        assert response.data["mfa_required"] is True


class TestRefresh:
    def test_refresh_without_csrf_header_is_rejected(
        self, api_client: APIClient, user: AbstractUser
    ) -> None:
        _login(api_client)

        response = api_client.post("/auth/refresh/")

        assert response.status_code == 403

    def test_refresh_with_valid_csrf_rotates_the_token(
        self, api_client: APIClient, user: AbstractUser
    ) -> None:
        login_response = _login(api_client)
        old_refresh_cookie = login_response.cookies["refresh_token"].value

        response = api_client.post("/auth/refresh/", **_csrf_headers(api_client))

        assert response.status_code == 200
        assert "access_token" in response.data
        assert response.cookies["refresh_token"].value != old_refresh_cookie

    def test_replaying_a_rotated_refresh_token_is_rejected_and_clears_cookies(
        self, api_client: APIClient, user: AbstractUser
    ) -> None:
        _login(api_client)
        old_refresh_cookie = api_client.cookies["refresh_token"].value

        api_client.post("/auth/refresh/", **_csrf_headers(api_client))  # legitimate rotation

        # Simulate an attacker replaying the pre-rotation cookie. The CSRF
        # cookie/header pair is re-read fresh here (rotation also rotates
        # it), so this exercises the refresh-token reuse check specifically
        # rather than an incidental CSRF mismatch.
        api_client.cookies["refresh_token"] = old_refresh_cookie
        response = api_client.post("/auth/refresh/", **_csrf_headers(api_client))

        assert response.status_code == 401
        assert response.cookies["refresh_token"]["max-age"] == 0

    def test_no_refresh_cookie_is_rejected(self, api_client: APIClient) -> None:
        response = api_client.post("/auth/refresh/", HTTP_X_REFRESH_CSRFTOKEN="anything")

        assert response.status_code in (401, 403)


class TestLogout:
    def test_logout_revokes_the_device_and_clears_cookies(
        self, api_client: APIClient, user: AbstractUser
    ) -> None:
        _login(api_client)
        headers = _csrf_headers(api_client)

        response = api_client.post("/auth/logout/", **headers)

        assert response.status_code == 200
        assert response.cookies["refresh_token"]["max-age"] == 0
        device = Device.objects.get(user=user)
        assert device.is_active is False

    def test_refresh_after_logout_is_rejected(
        self, api_client: APIClient, user: AbstractUser
    ) -> None:
        _login(api_client)
        headers = _csrf_headers(api_client)
        api_client.post("/auth/logout/", **headers)

        # Logout clears the CSRF cookie too, so a subsequent refresh with the
        # stale header is rejected at the CSRF check (403) before it would
        # even reach token validation (401) - both are "rejected".
        response = api_client.post("/auth/refresh/", **headers)

        assert response.status_code in (401, 403)


class TestLogoutAll:
    def test_requires_authentication(self, api_client: APIClient) -> None:
        response = api_client.post("/auth/logout-all/")

        assert response.status_code in (401, 403)

    def test_revokes_every_device(self, api_client: APIClient, user: AbstractUser) -> None:
        login_response = _login(api_client)
        access_token = login_response.data["access_token"]
        Device.objects.create(user=user, label="Another device")

        response = api_client.post("/auth/logout-all/", HTTP_AUTHORIZATION=f"Bearer {access_token}")

        assert response.status_code == 200
        assert response.data["revoked_devices"] == 2
        assert not Device.objects.filter(user=user, revoked_at__isnull=True).exists()


class TestDeviceEndpoints:
    def test_list_requires_authentication(self, api_client: APIClient) -> None:
        response = api_client.get("/auth/devices/")

        assert response.status_code in (401, 403)

    def test_list_returns_only_own_active_devices(
        self, authenticated_client: APIClient, user: AbstractUser, other_user: AbstractUser
    ) -> None:
        Device.objects.create(user=user)
        Device.objects.create(user=other_user)

        response = authenticated_client.get("/auth/devices/")

        assert response.status_code == 200
        assert len(response.data) == 1

    def test_revoking_a_device_marks_it_revoked(
        self, authenticated_client: APIClient, user: AbstractUser
    ) -> None:
        device = Device.objects.create(user=user)

        response = authenticated_client.delete(f"/auth/devices/{device.pk}/")

        assert response.status_code == 204
        device.refresh_from_db()
        assert device.is_active is False

    def test_cannot_revoke_another_users_device(
        self, authenticated_client: APIClient, other_user: AbstractUser
    ) -> None:
        device = Device.objects.create(user=other_user)

        response = authenticated_client.delete(f"/auth/devices/{device.pk}/")

        assert response.status_code == 404


class TestLoginHistoryEndpoint:
    def test_lists_only_own_history(
        self, authenticated_client: APIClient, user: AbstractUser, other_user: AbstractUser
    ) -> None:
        LoginHistory.objects.create(user=user, username_attempted="ada", success=True)
        LoginHistory.objects.create(user=other_user, username_attempted="grace", success=True)

        response = authenticated_client.get("/auth/login-history/")

        assert response.status_code == 200
        assert len(response.data) == 1


class TestTotpEnrollment:
    def test_setup_returns_secret_and_uri(self, authenticated_client: APIClient) -> None:
        response = authenticated_client.post("/auth/mfa/totp/setup/")

        assert response.status_code == 200
        assert re.fullmatch(r"[A-Z2-7]+", response.data["secret"])
        assert response.data["provisioning_uri"].startswith("otpauth://totp/")

    def test_confirm_requires_a_valid_code(
        self, authenticated_client: APIClient, user: AbstractUser
    ) -> None:
        setup_response = authenticated_client.post("/auth/mfa/totp/setup/")
        secret = setup_response.data["secret"]
        code = generate_totp_code(secret)

        response = authenticated_client.post("/auth/mfa/totp/confirm/", {"code": code})

        assert response.status_code == 200
        totp_device = TOTPDevice.objects.get(user=user)
        assert totp_device.confirmed is True

    def test_confirm_rejects_wrong_code(self, authenticated_client: APIClient) -> None:
        authenticated_client.post("/auth/mfa/totp/setup/")

        response = authenticated_client.post("/auth/mfa/totp/confirm/", {"code": "000000"})

        assert response.status_code == 400

    def test_disable_removes_the_device(
        self, authenticated_client: APIClient, user: AbstractUser
    ) -> None:
        setup_response = authenticated_client.post("/auth/mfa/totp/setup/")
        secret = setup_response.data["secret"]
        authenticated_client.post("/auth/mfa/totp/confirm/", {"code": generate_totp_code(secret)})

        response = authenticated_client.post("/auth/mfa/totp/disable/")

        assert response.status_code == 200
        assert not TOTPDevice.objects.filter(user=user).exists()

    def test_disable_when_not_enabled_returns_400(self, authenticated_client: APIClient) -> None:
        response = authenticated_client.post("/auth/mfa/totp/disable/")

        assert response.status_code == 400


class TestRefreshTokenRowLifecycle:
    def test_full_login_refresh_logout_cycle_leaves_a_clean_audit_trail(
        self, api_client: APIClient, user: AbstractUser
    ) -> None:
        _login(api_client)
        api_client.post("/auth/refresh/", **_csrf_headers(api_client))
        api_client.post("/auth/logout/", **_csrf_headers(api_client))

        device = Device.objects.get(user=user)
        tokens = list(RefreshToken.objects.filter(device=device).order_by("issued_at"))
        assert len(tokens) == 2
        assert tokens[0].revoked_reason == "rotated"
        assert tokens[1].revoked_reason == "logout"
