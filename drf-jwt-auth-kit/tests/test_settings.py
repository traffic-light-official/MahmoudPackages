"""Tests for :mod:`drf_jwt_auth_kit.settings`."""

from __future__ import annotations

import datetime as dt

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from drf_jwt_auth_kit.settings import (
    _TYPE_CHECKS,
    DEFAULTS,
    get_setting,
    get_signing_key,
    get_verifying_key,
)


class TestDefaults:
    def test_get_setting_returns_default_when_unconfigured(self) -> None:
        assert get_setting("ACCESS_TOKEN_LIFETIME") == dt.timedelta(minutes=5)
        assert get_setting("ALGORITHM") == "HS256"

    def test_get_setting_raises_key_error_for_unknown_setting(self) -> None:
        with pytest.raises(KeyError):
            get_setting("NOT_A_REAL_SETTING")

    def test_every_default_key_has_a_type_check(self) -> None:
        assert set(DEFAULTS) == set(_TYPE_CHECKS)


class TestSigningKey:
    def test_falls_back_to_secret_key_when_unset(self) -> None:
        assert get_signing_key() == "test-secret-key-not-for-production"

    def test_uses_explicit_signing_key_when_set(self) -> None:
        with override_settings(JWT_AUTH_KIT={"SIGNING_KEY": "explicit-key"}):
            assert get_signing_key() == "explicit-key"

    def test_verifying_key_falls_back_to_signing_key(self) -> None:
        with override_settings(JWT_AUTH_KIT={"SIGNING_KEY": "explicit-key"}):
            assert get_verifying_key() == "explicit-key"

    def test_verifying_key_can_differ_from_signing_key(self) -> None:
        with override_settings(
            JWT_AUTH_KIT={"SIGNING_KEY": "private-key", "VERIFYING_KEY": "public-key"}
        ):
            assert get_signing_key() == "private-key"
            assert get_verifying_key() == "public-key"


class TestUserOverrides:
    def test_override_settings_is_honored(self) -> None:
        with override_settings(JWT_AUTH_KIT={"ALGORITHM": "HS384"}):
            assert get_setting("ALGORITHM") == "HS384"

        assert get_setting("ALGORITHM") == "HS256"

    def test_non_dict_setting_raises_improperly_configured(self) -> None:
        with (
            override_settings(JWT_AUTH_KIT="not-a-dict"),
            pytest.raises(ImproperlyConfigured, match="must be a dict"),
        ):
            get_setting("ALGORITHM")

    def test_unknown_key_raises_improperly_configured(self) -> None:
        with (
            override_settings(JWT_AUTH_KIT={"NOT_REAL": True}),
            pytest.raises(ImproperlyConfigured, match="Unknown key"),
        ):
            get_setting("ALGORITHM")

    def test_wrong_type_raises_improperly_configured(self) -> None:
        with (
            override_settings(JWT_AUTH_KIT={"ALGORITHM": 123}),
            pytest.raises(ImproperlyConfigured, match="must be of type"),
        ):
            get_setting("ALGORITHM")

    def test_samesite_must_be_valid(self) -> None:
        with (
            override_settings(JWT_AUTH_KIT={"REFRESH_COOKIE_SAMESITE": "Sideways"}),
            pytest.raises(ImproperlyConfigured, match="REFRESH_COOKIE_SAMESITE"),
        ):
            get_setting("REFRESH_COOKIE_SAMESITE")

    def test_samesite_none_requires_secure(self) -> None:
        with (
            override_settings(
                JWT_AUTH_KIT={"REFRESH_COOKIE_SAMESITE": "None", "REFRESH_COOKIE_SECURE": False}
            ),
            pytest.raises(ImproperlyConfigured, match="requires"),
        ):
            get_setting("REFRESH_COOKIE_SAMESITE")

    def test_samesite_none_with_secure_is_accepted(self) -> None:
        with override_settings(
            JWT_AUTH_KIT={"REFRESH_COOKIE_SAMESITE": "None", "REFRESH_COOKIE_SECURE": True}
        ):
            assert get_setting("REFRESH_COOKIE_SAMESITE") == "None"

    def test_negative_totp_window_raises(self) -> None:
        with (
            override_settings(JWT_AUTH_KIT={"TOTP_VALID_WINDOW": -1}),
            pytest.raises(ImproperlyConfigured, match="TOTP_VALID_WINDOW"),
        ):
            get_setting("TOTP_VALID_WINDOW")
