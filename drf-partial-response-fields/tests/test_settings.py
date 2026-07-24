"""Unit tests for Django settings integration."""

from __future__ import annotations

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from drf_partial_response_fields.settings import get_setting


class TestDefaults:
    def test_default_query_param(self) -> None:
        assert get_setting("QUERY_PARAM") == "fields"

    def test_default_strict_is_false(self) -> None:
        assert get_setting("STRICT") is False

    def test_default_max_depth(self) -> None:
        assert get_setting("MAX_DEPTH") == 6

    def test_default_safe_methods_only_is_true(self) -> None:
        assert get_setting("SAFE_METHODS_ONLY") is True

    def test_invalid_key_raises_key_error(self) -> None:
        with pytest.raises(KeyError):
            get_setting("NOT_A_REAL_SETTING")


class TestOverrides:
    def test_override_query_param(self) -> None:
        with override_settings(PARTIAL_RESPONSE_FIELDS={"QUERY_PARAM": "select"}):
            assert get_setting("QUERY_PARAM") == "select"
        assert get_setting("QUERY_PARAM") == "fields"

    def test_override_strict(self) -> None:
        with override_settings(PARTIAL_RESPONSE_FIELDS={"STRICT": True}):
            assert get_setting("STRICT") is True

    def test_partial_override_keeps_other_defaults(self) -> None:
        with override_settings(PARTIAL_RESPONSE_FIELDS={"STRICT": True}):
            assert get_setting("MAX_DEPTH") == 6


class TestValidation:
    def test_non_dict_setting_raises(self) -> None:
        with (
            override_settings(PARTIAL_RESPONSE_FIELDS="not-a-dict"),
            pytest.raises(ImproperlyConfigured),
        ):
            get_setting("QUERY_PARAM")

    def test_unknown_key_raises(self) -> None:
        with (
            override_settings(PARTIAL_RESPONSE_FIELDS={"NOT_REAL": 1}),
            pytest.raises(ImproperlyConfigured),
        ):
            get_setting("QUERY_PARAM")

    def test_wrong_type_raises(self) -> None:
        with (
            override_settings(PARTIAL_RESPONSE_FIELDS={"STRICT": "yes"}),
            pytest.raises(ImproperlyConfigured),
        ):
            get_setting("STRICT")

    def test_max_depth_below_one_raises(self) -> None:
        with (
            override_settings(PARTIAL_RESPONSE_FIELDS={"MAX_DEPTH": 0}),
            pytest.raises(ImproperlyConfigured),
        ):
            get_setting("MAX_DEPTH")

    def test_invalid_query_param_identifier_raises(self) -> None:
        with (
            override_settings(PARTIAL_RESPONSE_FIELDS={"QUERY_PARAM": "not valid!"}),
            pytest.raises(ImproperlyConfigured),
        ):
            get_setting("QUERY_PARAM")

    def test_max_fields_length_below_one_raises(self) -> None:
        with (
            override_settings(PARTIAL_RESPONSE_FIELDS={"MAX_FIELDS_LENGTH": 0}),
            pytest.raises(ImproperlyConfigured),
        ):
            get_setting("MAX_FIELDS_LENGTH")


class TestSettingChangedSignal:
    def test_unrelated_setting_change_does_not_invalidate_cache(self) -> None:
        # Prime the cache, then trigger the setting_changed signal for an
        # unrelated setting - our cached value must survive untouched.
        assert get_setting("QUERY_PARAM") == "fields"
        with override_settings(SOME_OTHER_UNRELATED_SETTING="value"):
            assert get_setting("QUERY_PARAM") == "fields"
