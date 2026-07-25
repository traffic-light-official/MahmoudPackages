"""Tests for :mod:`drf_bulk_operations.settings`."""

from __future__ import annotations

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from drf_bulk_operations.settings import get_setting


class TestDefaults:
    def test_max_batch_size_default(self) -> None:
        assert get_setting("MAX_BATCH_SIZE") == 100

    def test_atomic_default(self) -> None:
        assert get_setting("ATOMIC") is True

    def test_invalid_key_raises_key_error(self) -> None:
        with pytest.raises(KeyError):
            get_setting("NOT_A_REAL_SETTING")


class TestOverrides:
    def test_override_settings_changes_the_effective_value(self) -> None:
        with override_settings(BULK_OPERATIONS={"ATOMIC": False}):
            assert get_setting("ATOMIC") is False
        assert get_setting("ATOMIC") is True

    def test_non_dict_setting_raises_improperly_configured(self) -> None:
        with (
            override_settings(BULK_OPERATIONS="not-a-dict"),
            pytest.raises(ImproperlyConfigured, match="must be a dict"),
        ):
            get_setting("ATOMIC")

    def test_unknown_key_raises_improperly_configured(self) -> None:
        with (
            override_settings(BULK_OPERATIONS={"NOT_REAL": 1}),
            pytest.raises(ImproperlyConfigured, match="Unknown key"),
        ):
            get_setting("ATOMIC")

    def test_wrong_type_raises_improperly_configured(self) -> None:
        with (
            override_settings(BULK_OPERATIONS={"ATOMIC": "yes"}),
            pytest.raises(ImproperlyConfigured, match="must be of type"),
        ):
            get_setting("ATOMIC")

    def test_zero_max_batch_size_raises_improperly_configured(self) -> None:
        with (
            override_settings(BULK_OPERATIONS={"MAX_BATCH_SIZE": 0}),
            pytest.raises(ImproperlyConfigured, match="at least 1"),
        ):
            get_setting("MAX_BATCH_SIZE")

    def test_negative_max_batch_size_raises_improperly_configured(self) -> None:
        with (
            override_settings(BULK_OPERATIONS={"MAX_BATCH_SIZE": -5}),
            pytest.raises(ImproperlyConfigured, match="at least 1"),
        ):
            get_setting("MAX_BATCH_SIZE")

    def test_an_unrelated_setting_change_does_not_invalidate_the_cache(self) -> None:
        with override_settings(BULK_OPERATIONS={"ATOMIC": False}):
            assert get_setting("ATOMIC") is False
            with override_settings(DEBUG=True):
                assert get_setting("ATOMIC") is False
            assert get_setting("ATOMIC") is False
