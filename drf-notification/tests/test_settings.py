"""Tests for :mod:`drf_notification.settings`."""

from __future__ import annotations

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from drf_notification.constants import CHANNEL_EMAIL
from drf_notification.settings import _TYPE_CHECKS, DEFAULTS, get_setting


class TestDefaults:
    def test_get_setting_returns_default_when_unconfigured(self) -> None:
        assert get_setting("MAX_RETRIES") == 3
        assert get_setting("USE_CELERY") is False

    def test_get_setting_raises_key_error_for_unknown_setting(self) -> None:
        with pytest.raises(KeyError):
            get_setting("NOT_A_REAL_SETTING")

    def test_every_default_key_has_a_type_check(self) -> None:
        assert set(DEFAULTS) == set(_TYPE_CHECKS)

    def test_default_backends_cover_every_channel(self) -> None:
        backends = get_setting("BACKENDS")
        assert CHANNEL_EMAIL in backends


class TestUserOverrides:
    def test_override_settings_is_honored(self) -> None:
        with override_settings(NOTIFICATIONS={"MAX_RETRIES": 5}):
            assert get_setting("MAX_RETRIES") == 5

        assert get_setting("MAX_RETRIES") == 3

    def test_dict_settings_are_deep_merged_not_replaced(self) -> None:
        with override_settings(NOTIFICATIONS={"RATE_LIMITS": {CHANNEL_EMAIL: "5/day"}}):
            limits = get_setting("RATE_LIMITS")
            assert limits[CHANNEL_EMAIL] == "5/day"
            assert "sms" in limits  # untouched default key still present

    def test_non_dict_setting_raises_improperly_configured(self) -> None:
        with (
            override_settings(NOTIFICATIONS="not-a-dict"),
            pytest.raises(ImproperlyConfigured, match="must be a dict"),
        ):
            get_setting("MAX_RETRIES")

    def test_unknown_key_raises_improperly_configured(self) -> None:
        with (
            override_settings(NOTIFICATIONS={"NOT_REAL": True}),
            pytest.raises(ImproperlyConfigured, match="Unknown key"),
        ):
            get_setting("MAX_RETRIES")

    def test_wrong_type_raises_improperly_configured(self) -> None:
        with (
            override_settings(NOTIFICATIONS={"MAX_RETRIES": "five"}),
            pytest.raises(ImproperlyConfigured, match="must be of type"),
        ):
            get_setting("MAX_RETRIES")

    def test_negative_max_retries_raises_improperly_configured(self) -> None:
        with (
            override_settings(NOTIFICATIONS={"MAX_RETRIES": -1}),
            pytest.raises(ImproperlyConfigured, match="MAX_RETRIES"),
        ):
            get_setting("MAX_RETRIES")
