"""Tests for :mod:`drf_jwt_auth_kit.mfa`."""

from __future__ import annotations

import pytest
from django.contrib.auth.models import AbstractUser
from django.test import override_settings

from drf_jwt_auth_kit.mfa import (
    NullMFAProvider,
    TOTPProvider,
    generate_totp_code,
    generate_totp_secret,
    get_mfa_provider,
    totp_provisioning_uri,
    verify_totp_code,
)
from drf_jwt_auth_kit.models import TOTPDevice

pytestmark = pytest.mark.django_db


class TestNullMFAProvider:
    def test_never_requires_mfa(self, user: AbstractUser) -> None:
        provider = NullMFAProvider()

        assert provider.is_required(user) is False

    def test_verify_always_true(self, user: AbstractUser) -> None:
        provider = NullMFAProvider()

        assert provider.verify(user, "anything") is True


class TestGetMfaProvider:
    def test_defaults_to_null_provider(self) -> None:
        # The test project configures MFA_PROVIDER = TOTPProvider (see
        # tests/test_app/settings.py) so integration tests can exercise MFA;
        # this test asserts the *package's own* default absent that override.
        with override_settings(
            JWT_AUTH_KIT={"MFA_PROVIDER": "drf_jwt_auth_kit.mfa.NullMFAProvider"}
        ):
            assert isinstance(get_mfa_provider(), NullMFAProvider)

    def test_resolves_a_configured_provider(self) -> None:
        with override_settings(JWT_AUTH_KIT={"MFA_PROVIDER": "drf_jwt_auth_kit.mfa.TOTPProvider"}):
            assert isinstance(get_mfa_provider(), TOTPProvider)


class TestTotpSecretAndUri:
    def test_generate_totp_secret_is_base32(self) -> None:
        secret = generate_totp_secret()

        assert secret == secret.upper()
        assert all(char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567" for char in secret)

    def test_generate_totp_secret_is_random(self) -> None:
        assert generate_totp_secret() != generate_totp_secret()

    def test_provisioning_uri_contains_secret_and_issuer(self) -> None:
        uri = totp_provisioning_uri(secret="JBSWY3DPEHPK3PXP", account_name="ada@example.com")

        assert uri.startswith("otpauth://totp/")
        assert "secret=JBSWY3DPEHPK3PXP" in uri
        assert "issuer=drf-jwt-auth-kit" in uri
        assert "ada%40example.com" in uri or "ada@example.com" in uri


class TestGenerateAndVerifyTotpCode:
    def test_code_is_six_digits(self) -> None:
        code = generate_totp_code("JBSWY3DPEHPK3PXP", at=1_700_000_000)

        assert len(code) == 6
        assert code.isdigit()

    def test_code_is_deterministic_for_a_given_secret_and_time(self) -> None:
        secret = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"

        assert generate_totp_code(secret, at=59) == generate_totp_code(secret, at=59)
        assert generate_totp_code(secret, at=59) != generate_totp_code(secret, at=999_999)

    def test_verify_accepts_code_within_the_default_window(self) -> None:
        secret = generate_totp_secret()
        code = generate_totp_code(secret, at=1_700_000_000)

        # One 30-second step later, still within the default window of 1.
        assert verify_totp_code(secret, code, at=1_700_000_000 + 30) is True

    def test_verify_rejects_code_outside_the_window(self) -> None:
        secret = generate_totp_secret()
        code = generate_totp_code(secret, at=1_700_000_000)

        assert verify_totp_code(secret, code, at=1_700_000_000 + 300) is False

    def test_verify_rejects_wrong_code(self) -> None:
        secret = generate_totp_secret()

        assert verify_totp_code(secret, "000000", at=1_700_000_000) is False

    def test_verify_rejects_non_numeric_code(self) -> None:
        secret = generate_totp_secret()

        assert verify_totp_code(secret, "abcdef", at=1_700_000_000) is False

    def test_verify_rejects_wrong_length_code(self) -> None:
        secret = generate_totp_secret()

        assert verify_totp_code(secret, "123", at=1_700_000_000) is False

    def test_custom_window_widens_tolerance(self) -> None:
        secret = generate_totp_secret()
        code = generate_totp_code(secret, at=1_700_000_000)

        with override_settings(JWT_AUTH_KIT={"TOTP_VALID_WINDOW": 5}):
            assert verify_totp_code(secret, code, at=1_700_000_000 + 150) is True


class TestTotpProvider:
    def test_is_required_false_without_a_confirmed_device(self, user: AbstractUser) -> None:
        provider = TOTPProvider()

        assert provider.is_required(user) is False

    def test_is_required_false_when_device_unconfirmed(self, user: AbstractUser) -> None:
        TOTPDevice.objects.create(user=user, secret=generate_totp_secret(), confirmed=False)

        assert TOTPProvider().is_required(user) is False

    def test_is_required_true_once_confirmed(self, user: AbstractUser) -> None:
        TOTPDevice.objects.create(user=user, secret=generate_totp_secret(), confirmed=True)

        assert TOTPProvider().is_required(user) is True

    def test_verify_uses_the_users_secret(self, user: AbstractUser) -> None:
        secret = generate_totp_secret()
        TOTPDevice.objects.create(user=user, secret=secret, confirmed=True)
        # TOTPProvider.verify() always checks against the real current time
        # (it has no `at` override), so the code must be generated the same way.
        code = generate_totp_code(secret)

        assert TOTPProvider().verify(user, code) is True

    def test_verify_false_when_no_confirmed_device(self, user: AbstractUser) -> None:
        assert TOTPProvider().verify(user, "123456") is False
