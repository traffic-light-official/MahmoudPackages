"""Tests for :mod:`drf_permission_debugger.settings`."""

from __future__ import annotations

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from drf_permission_debugger.settings import get_setting


class TestDefaults:
    def test_enabled_default(self) -> None:
        assert get_setting("ENABLED") is False

    def test_restrict_to_staff_default(self) -> None:
        assert get_setting("RESTRICT_TO_STAFF") is True

    def test_header_name_default(self) -> None:
        assert get_setting("HEADER_NAME") == "X-Permission-Trace"

    def test_include_in_response_body_default(self) -> None:
        assert get_setting("INCLUDE_IN_RESPONSE_BODY") is False

    def test_invalid_key_raises_key_error(self) -> None:
        with pytest.raises(KeyError):
            get_setting("NOT_A_REAL_SETTING")


class TestOverrides:
    def test_override_settings_changes_the_effective_value(self) -> None:
        with override_settings(PERMISSION_DEBUGGER={"ENABLED": True}):
            assert get_setting("ENABLED") is True
        assert get_setting("ENABLED") is False

    def test_non_dict_setting_raises_improperly_configured(self) -> None:
        with (
            override_settings(PERMISSION_DEBUGGER="not-a-dict"),
            pytest.raises(ImproperlyConfigured, match="must be a dict"),
        ):
            get_setting("ENABLED")

    def test_unknown_key_raises_improperly_configured(self) -> None:
        with (
            override_settings(PERMISSION_DEBUGGER={"NOT_REAL": 1}),
            pytest.raises(ImproperlyConfigured, match="Unknown key"),
        ):
            get_setting("ENABLED")

    def test_wrong_type_raises_improperly_configured(self) -> None:
        with (
            override_settings(PERMISSION_DEBUGGER={"ENABLED": "yes"}),
            pytest.raises(ImproperlyConfigured, match="must be of type"),
        ):
            get_setting("ENABLED")

    def test_empty_header_name_raises_improperly_configured(self) -> None:
        with (
            override_settings(PERMISSION_DEBUGGER={"HEADER_NAME": ""}),
            pytest.raises(ImproperlyConfigured, match="cannot be empty"),
        ):
            get_setting("HEADER_NAME")

    def test_an_unrelated_setting_change_does_not_invalidate_the_cache(self) -> None:
        with override_settings(PERMISSION_DEBUGGER={"ENABLED": True}):
            assert get_setting("ENABLED") is True
            with override_settings(DEBUG=True):
                assert get_setting("ENABLED") is True
            assert get_setting("ENABLED") is True
