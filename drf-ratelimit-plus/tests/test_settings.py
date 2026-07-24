"""Unit tests for Django settings integration."""

from __future__ import annotations

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from drf_ratelimit_plus.settings import get_setting


class TestDefaults:
    def test_default_redis_url(self) -> None:
        # The test settings module overrides REDIS_URL project-wide (see
        # tests/test_app/settings.py), so assert the *default* in
        # isolation by clearing that override for this one check.
        with override_settings(RATELIMIT_PLUS={}):
            assert get_setting("REDIS_URL") == "redis://localhost:6379/0"

    def test_default_key_prefix(self) -> None:
        assert get_setting("KEY_PREFIX") == "ratelimit-plus:"

    def test_default_limit_header(self) -> None:
        assert get_setting("LIMIT_HEADER") == "RateLimit-Limit"

    def test_invalid_key_raises_key_error(self) -> None:
        with pytest.raises(KeyError):
            get_setting("NOT_A_REAL_SETTING")


class TestOverrides:
    def test_override_key_prefix(self) -> None:
        with override_settings(RATELIMIT_PLUS={"KEY_PREFIX": "myapp:"}):
            assert get_setting("KEY_PREFIX") == "myapp:"
        assert get_setting("KEY_PREFIX") == "ratelimit-plus:"


class TestValidation:
    def test_non_dict_setting_raises(self) -> None:
        with (
            override_settings(RATELIMIT_PLUS="not-a-dict"),
            pytest.raises(ImproperlyConfigured),
        ):
            get_setting("KEY_PREFIX")

    def test_unknown_key_raises(self) -> None:
        with (
            override_settings(RATELIMIT_PLUS={"NOT_REAL": 1}),
            pytest.raises(ImproperlyConfigured),
        ):
            get_setting("KEY_PREFIX")

    def test_wrong_type_raises(self) -> None:
        with (
            override_settings(RATELIMIT_PLUS={"KEY_PREFIX": 123}),
            pytest.raises(ImproperlyConfigured),
        ):
            get_setting("KEY_PREFIX")

    def test_empty_key_prefix_raises(self) -> None:
        with (
            override_settings(RATELIMIT_PLUS={"KEY_PREFIX": ""}),
            pytest.raises(ImproperlyConfigured),
        ):
            get_setting("KEY_PREFIX")
