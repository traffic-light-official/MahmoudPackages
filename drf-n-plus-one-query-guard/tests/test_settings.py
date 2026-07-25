"""Tests for :mod:`drf_n_plus_one_query_guard.settings`."""

from __future__ import annotations

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from drf_n_plus_one_query_guard.settings import get_setting


class TestDefaults:
    def test_threshold_default(self) -> None:
        assert get_setting("THRESHOLD") == 2

    def test_mode_default(self) -> None:
        assert get_setting("MODE") == "report"  # overridden in tests/test_app/settings.py

    def test_ignore_patterns_default_is_empty(self) -> None:
        assert get_setting("IGNORE_PATTERNS") == []

    def test_invalid_key_raises_key_error(self) -> None:
        with pytest.raises(KeyError):
            get_setting("NOT_A_REAL_SETTING")


class TestOverrides:
    def test_override_settings_changes_the_effective_value(self) -> None:
        with override_settings(N_PLUS_ONE_GUARD={"THRESHOLD": 5}):
            assert get_setting("THRESHOLD") == 5
        assert get_setting("THRESHOLD") == 2

    def test_non_dict_setting_raises_improperly_configured(self) -> None:
        with override_settings(N_PLUS_ONE_GUARD="not-a-dict"), pytest.raises(ImproperlyConfigured):
            get_setting("THRESHOLD")

    def test_unknown_key_raises_improperly_configured(self) -> None:
        with (
            override_settings(N_PLUS_ONE_GUARD={"NOT_REAL": 1}),
            pytest.raises(ImproperlyConfigured, match="Unknown key"),
        ):
            get_setting("THRESHOLD")

    def test_wrong_type_raises_improperly_configured(self) -> None:
        with (
            override_settings(N_PLUS_ONE_GUARD={"THRESHOLD": "two"}),
            pytest.raises(ImproperlyConfigured, match="must be of type"),
        ):
            get_setting("THRESHOLD")

    def test_threshold_below_two_raises_improperly_configured(self) -> None:
        with (
            override_settings(N_PLUS_ONE_GUARD={"THRESHOLD": 1}),
            pytest.raises(ImproperlyConfigured, match="at least 2"),
        ):
            get_setting("THRESHOLD")

    def test_invalid_mode_raises_improperly_configured(self) -> None:
        with (
            override_settings(N_PLUS_ONE_GUARD={"MODE": "explode"}),
            pytest.raises(ImproperlyConfigured, match="must be one of"),
        ):
            get_setting("MODE")

    def test_invalid_ignore_pattern_type_raises_improperly_configured(self) -> None:
        with (
            override_settings(N_PLUS_ONE_GUARD={"IGNORE_PATTERNS": [123]}),
            pytest.raises(ImproperlyConfigured, match="entries must be strings"),
        ):
            get_setting("IGNORE_PATTERNS")

    def test_invalid_regex_raises_improperly_configured(self) -> None:
        with (
            override_settings(N_PLUS_ONE_GUARD={"IGNORE_PATTERNS": ["("]}),
            pytest.raises(ImproperlyConfigured, match="invalid regular expression"),
        ):
            get_setting("IGNORE_PATTERNS")
