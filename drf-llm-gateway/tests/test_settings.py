"""Unit tests for Django settings integration."""

from __future__ import annotations

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from drf_llm_gateway.settings import get_setting


class TestDefaults:
    def test_default_name_separator(self) -> None:
        assert get_setting("NAME_SEPARATOR") == "_"

    def test_default_max_enum_values(self) -> None:
        assert get_setting("MAX_ENUM_VALUES") == 100

    def test_default_enforce_permissions(self) -> None:
        assert get_setting("ENFORCE_PERMISSIONS") is True

    def test_invalid_key_raises_key_error(self) -> None:
        with pytest.raises(KeyError):
            get_setting("NOT_A_REAL_SETTING")


class TestOverrides:
    def test_override_name_separator(self) -> None:
        with override_settings(LLM_GATEWAY={"NAME_SEPARATOR": "."}):
            assert get_setting("NAME_SEPARATOR") == "."
        assert get_setting("NAME_SEPARATOR") == "_"

    def test_partial_override_keeps_other_defaults(self) -> None:
        with override_settings(LLM_GATEWAY={"NAME_SEPARATOR": "."}):
            assert get_setting("MAX_ENUM_VALUES") == 100


class TestValidation:
    def test_non_dict_setting_raises(self) -> None:
        with (
            override_settings(LLM_GATEWAY="not-a-dict"),
            pytest.raises(ImproperlyConfigured),
        ):
            get_setting("NAME_SEPARATOR")

    def test_unknown_key_raises(self) -> None:
        with (
            override_settings(LLM_GATEWAY={"NOT_REAL": 1}),
            pytest.raises(ImproperlyConfigured),
        ):
            get_setting("NAME_SEPARATOR")

    def test_wrong_type_raises(self) -> None:
        with (
            override_settings(LLM_GATEWAY={"ENFORCE_PERMISSIONS": "yes"}),
            pytest.raises(ImproperlyConfigured),
        ):
            get_setting("ENFORCE_PERMISSIONS")

    def test_max_enum_values_below_one_raises(self) -> None:
        with (
            override_settings(LLM_GATEWAY={"MAX_ENUM_VALUES": 0}),
            pytest.raises(ImproperlyConfigured),
        ):
            get_setting("MAX_ENUM_VALUES")

    def test_max_schema_depth_below_one_raises(self) -> None:
        with (
            override_settings(LLM_GATEWAY={"MAX_SCHEMA_DEPTH": 0}),
            pytest.raises(ImproperlyConfigured),
        ):
            get_setting("MAX_SCHEMA_DEPTH")

    def test_empty_name_separator_raises(self) -> None:
        with (
            override_settings(LLM_GATEWAY={"NAME_SEPARATOR": ""}),
            pytest.raises(ImproperlyConfigured),
        ):
            get_setting("NAME_SEPARATOR")
