"""Tests for :mod:`drf_serializer_performance_profiler.settings`."""

from __future__ import annotations

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from drf_serializer_performance_profiler.settings import get_setting


class TestDefaults:
    def test_enabled_default(self) -> None:
        assert get_setting("ENABLED") is False

    def test_restrict_to_staff_default(self) -> None:
        assert get_setting("RESTRICT_TO_STAFF") is True

    def test_header_name_default(self) -> None:
        assert get_setting("HEADER_NAME") == "X-Serializer-Profile"

    def test_log_slow_fields_default(self) -> None:
        assert get_setting("LOG_SLOW_FIELDS") is False

    def test_slow_field_threshold_ms_default(self) -> None:
        assert get_setting("SLOW_FIELD_THRESHOLD_MS") == 5.0

    def test_invalid_key_raises_key_error(self) -> None:
        with pytest.raises(KeyError):
            get_setting("NOT_A_REAL_SETTING")


class TestOverrides:
    def test_override_settings_changes_the_effective_value(self) -> None:
        with override_settings(SERIALIZER_PROFILER={"ENABLED": True}):
            assert get_setting("ENABLED") is True
        assert get_setting("ENABLED") is False

    def test_non_dict_setting_raises_improperly_configured(self) -> None:
        with (
            override_settings(SERIALIZER_PROFILER="not-a-dict"),
            pytest.raises(ImproperlyConfigured, match="must be a dict"),
        ):
            get_setting("ENABLED")

    def test_unknown_key_raises_improperly_configured(self) -> None:
        with (
            override_settings(SERIALIZER_PROFILER={"NOT_REAL": 1}),
            pytest.raises(ImproperlyConfigured, match="Unknown key"),
        ):
            get_setting("ENABLED")

    def test_wrong_type_raises_improperly_configured(self) -> None:
        with (
            override_settings(SERIALIZER_PROFILER={"ENABLED": "yes"}),
            pytest.raises(ImproperlyConfigured, match="must be of type"),
        ):
            get_setting("ENABLED")

    def test_bool_for_threshold_raises_improperly_configured(self) -> None:
        with (
            override_settings(SERIALIZER_PROFILER={"SLOW_FIELD_THRESHOLD_MS": True}),
            pytest.raises(ImproperlyConfigured, match="must be of type"),
        ):
            get_setting("SLOW_FIELD_THRESHOLD_MS")

    def test_negative_threshold_raises_improperly_configured(self) -> None:
        with (
            override_settings(SERIALIZER_PROFILER={"SLOW_FIELD_THRESHOLD_MS": -1.0}),
            pytest.raises(ImproperlyConfigured, match="cannot be negative"),
        ):
            get_setting("SLOW_FIELD_THRESHOLD_MS")

    def test_zero_threshold_is_allowed(self) -> None:
        with override_settings(SERIALIZER_PROFILER={"SLOW_FIELD_THRESHOLD_MS": 0.0}):
            assert get_setting("SLOW_FIELD_THRESHOLD_MS") == 0.0

    def test_empty_header_name_raises_improperly_configured(self) -> None:
        with (
            override_settings(SERIALIZER_PROFILER={"HEADER_NAME": ""}),
            pytest.raises(ImproperlyConfigured, match="cannot be empty"),
        ):
            get_setting("HEADER_NAME")

    def test_an_unrelated_setting_change_does_not_invalidate_the_cache(self) -> None:
        with override_settings(SERIALIZER_PROFILER={"ENABLED": True}):
            assert get_setting("ENABLED") is True
            with override_settings(DEBUG=True):
                assert get_setting("ENABLED") is True
            assert get_setting("ENABLED") is True
