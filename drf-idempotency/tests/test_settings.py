"""Unit tests for Django settings integration."""

from __future__ import annotations

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from drf_idempotency.settings import get_setting


class TestDefaults:
    def test_default_header_name(self) -> None:
        assert get_setting("HEADER_NAME") == "Idempotency-Key"

    def test_default_methods(self) -> None:
        assert get_setting("METHODS") == {"POST", "PUT", "PATCH"}

    def test_default_ttl(self) -> None:
        assert get_setting("TTL_SECONDS") == 86400

    def test_default_require_key_is_false(self) -> None:
        assert get_setting("REQUIRE_KEY") is False

    def test_invalid_key_raises_key_error(self) -> None:
        with pytest.raises(KeyError):
            get_setting("NOT_A_REAL_SETTING")


class TestOverrides:
    def test_override_header_name(self) -> None:
        with override_settings(IDEMPOTENCY={"HEADER_NAME": "X-Idempotency"}):
            assert get_setting("HEADER_NAME") == "X-Idempotency"
        assert get_setting("HEADER_NAME") == "Idempotency-Key"

    def test_methods_are_normalized_to_uppercase_set(self) -> None:
        with override_settings(IDEMPOTENCY={"METHODS": ["post", "delete"]}):
            assert get_setting("METHODS") == {"POST", "DELETE"}


class TestValidation:
    def test_non_dict_setting_raises(self) -> None:
        with (
            override_settings(IDEMPOTENCY="not-a-dict"),
            pytest.raises(ImproperlyConfigured),
        ):
            get_setting("HEADER_NAME")

    def test_unknown_key_raises(self) -> None:
        with (
            override_settings(IDEMPOTENCY={"NOT_REAL": 1}),
            pytest.raises(ImproperlyConfigured),
        ):
            get_setting("HEADER_NAME")

    def test_wrong_type_raises(self) -> None:
        with (
            override_settings(IDEMPOTENCY={"REQUIRE_KEY": "yes"}),
            pytest.raises(ImproperlyConfigured),
        ):
            get_setting("REQUIRE_KEY")

    def test_ttl_below_one_raises(self) -> None:
        with (
            override_settings(IDEMPOTENCY={"TTL_SECONDS": 0}),
            pytest.raises(ImproperlyConfigured),
        ):
            get_setting("TTL_SECONDS")

    def test_lock_ttl_below_one_raises(self) -> None:
        with (
            override_settings(IDEMPOTENCY={"LOCK_TTL_SECONDS": 0}),
            pytest.raises(ImproperlyConfigured),
        ):
            get_setting("LOCK_TTL_SECONDS")

    def test_max_key_length_below_one_raises(self) -> None:
        with (
            override_settings(IDEMPOTENCY={"MAX_KEY_LENGTH": 0}),
            pytest.raises(ImproperlyConfigured),
        ):
            get_setting("MAX_KEY_LENGTH")
