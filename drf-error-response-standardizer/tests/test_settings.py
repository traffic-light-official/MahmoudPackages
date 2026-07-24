"""Tests for :mod:`drf_error_response_standardizer.settings`."""

from __future__ import annotations

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from drf_error_response_standardizer.settings import DEFAULTS, get_setting


class TestDefaults:
    def test_get_setting_returns_default_when_unconfigured(self) -> None:
        assert get_setting("MEDIA_TYPE") == "application/problem+json"
        assert get_setting("CATCH_ALL_EXCEPTIONS") is True

    def test_get_setting_raises_key_error_for_unknown_setting(self) -> None:
        with pytest.raises(KeyError):
            get_setting("NOT_A_REAL_SETTING")

    def test_every_default_key_has_a_type_check(self) -> None:
        from drf_error_response_standardizer.settings import _TYPE_CHECKS

        assert set(DEFAULTS) == set(_TYPE_CHECKS)


class TestUserOverrides:
    def test_override_settings_is_honored(self) -> None:
        with override_settings(ERROR_RESPONSE_STANDARDIZER={"MEDIA_TYPE": "application/json"}):
            assert get_setting("MEDIA_TYPE") == "application/json"

        assert get_setting("MEDIA_TYPE") == "application/problem+json"

    def test_partial_override_keeps_other_defaults(self) -> None:
        with override_settings(ERROR_RESPONSE_STANDARDIZER={"INCLUDE_TIMESTAMP": False}):
            assert get_setting("INCLUDE_TIMESTAMP") is False
            assert get_setting("INCLUDE_TRACE_ID") is True

    def test_non_dict_setting_raises_improperly_configured(self) -> None:
        with (
            override_settings(ERROR_RESPONSE_STANDARDIZER="not-a-dict"),
            pytest.raises(ImproperlyConfigured, match="must be a dict"),
        ):
            get_setting("MEDIA_TYPE")

    def test_unknown_key_raises_improperly_configured(self) -> None:
        with (
            override_settings(ERROR_RESPONSE_STANDARDIZER={"NOT_REAL": True}),
            pytest.raises(ImproperlyConfigured, match="Unknown key"),
        ):
            get_setting("MEDIA_TYPE")

    def test_wrong_type_raises_improperly_configured(self) -> None:
        with (
            override_settings(ERROR_RESPONSE_STANDARDIZER={"INCLUDE_TIMESTAMP": "yes"}),
            pytest.raises(ImproperlyConfigured, match="must be of type"),
        ):
            get_setting("INCLUDE_TIMESTAMP")

    def test_type_base_uri_without_trailing_slash_raises(self) -> None:
        with (
            override_settings(
                ERROR_RESPONSE_STANDARDIZER={"TYPE_BASE_URI": "https://api.example.com/problems"}
            ),
            pytest.raises(ImproperlyConfigured, match="must end with"),
        ):
            get_setting("TYPE_BASE_URI")

    def test_type_base_uri_with_trailing_slash_is_accepted(self) -> None:
        with override_settings(
            ERROR_RESPONSE_STANDARDIZER={"TYPE_BASE_URI": "https://api.example.com/problems/"}
        ):
            assert get_setting("TYPE_BASE_URI") == "https://api.example.com/problems/"

    def test_type_base_uri_none_is_accepted(self) -> None:
        with override_settings(ERROR_RESPONSE_STANDARDIZER={"TYPE_BASE_URI": None}):
            assert get_setting("TYPE_BASE_URI") is None
