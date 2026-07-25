"""Tests for :mod:`drf_api_versioning.settings`."""

from __future__ import annotations

import datetime

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from drf_api_versioning.settings import get_setting


class TestDefaults:
    def test_default_version_from_test_settings(self) -> None:
        assert get_setting("DEFAULT_VERSION") == "v3"

    def test_allow_sunset_default(self) -> None:
        assert get_setting("ALLOW_SUNSET") is False

    def test_deprecation_header_default(self) -> None:
        assert get_setting("DEPRECATION_HEADER") == "Deprecation"

    def test_sunset_header_default(self) -> None:
        assert get_setting("SUNSET_HEADER") == "Sunset"

    def test_link_header_default(self) -> None:
        assert get_setting("LINK_HEADER") == "Link"

    def test_invalid_key_raises_key_error(self) -> None:
        with pytest.raises(KeyError):
            get_setting("NOT_A_REAL_SETTING")


class TestOverrides:
    def test_override_settings_changes_the_effective_value(self) -> None:
        with override_settings(API_VERSIONING={"VERSIONS": {"only": {}}, "ALLOW_SUNSET": True}):
            assert get_setting("ALLOW_SUNSET") is True
        assert get_setting("ALLOW_SUNSET") is False

    def test_non_dict_setting_raises_improperly_configured(self) -> None:
        with override_settings(API_VERSIONING="not-a-dict"), pytest.raises(ImproperlyConfigured):
            get_setting("VERSIONS")

    def test_unknown_key_raises_improperly_configured(self) -> None:
        with (
            override_settings(API_VERSIONING={"VERSIONS": {"only": {}}, "NOT_REAL": 1}),
            pytest.raises(ImproperlyConfigured, match="Unknown key"),
        ):
            get_setting("VERSIONS")

    def test_wrong_type_raises_improperly_configured(self) -> None:
        with (
            override_settings(API_VERSIONING={"VERSIONS": {"only": {}}, "ALLOW_SUNSET": "yes"}),
            pytest.raises(ImproperlyConfigured, match="must be of type"),
        ):
            get_setting("ALLOW_SUNSET")

    def test_empty_versions_raises_improperly_configured(self) -> None:
        with (
            override_settings(API_VERSIONING={"VERSIONS": {}}),
            pytest.raises(ImproperlyConfigured, match="at least one version"),
        ):
            get_setting("VERSIONS")

    def test_empty_string_version_key_raises_improperly_configured(self) -> None:
        with (
            override_settings(API_VERSIONING={"VERSIONS": {"": {}}}),
            pytest.raises(ImproperlyConfigured, match="non-empty strings"),
        ):
            get_setting("VERSIONS")

    def test_non_dict_version_entry_raises_improperly_configured(self) -> None:
        with (
            override_settings(API_VERSIONING={"VERSIONS": {"v1": "not-a-dict"}}),
            pytest.raises(ImproperlyConfigured, match="must be a dict"),
        ):
            get_setting("VERSIONS")

    def test_unknown_version_entry_key_raises_improperly_configured(self) -> None:
        with (
            override_settings(API_VERSIONING={"VERSIONS": {"v1": {"bogus": 1}}}),
            pytest.raises(ImproperlyConfigured, match="Unknown key"),
        ):
            get_setting("VERSIONS")

    def test_non_date_deprecated_raises_improperly_configured(self) -> None:
        with (
            override_settings(API_VERSIONING={"VERSIONS": {"v1": {"deprecated": "2026-01-01"}}}),
            pytest.raises(ImproperlyConfigured, match="must be"),
        ):
            get_setting("VERSIONS")

    def test_non_str_deprecation_link_raises_improperly_configured(self) -> None:
        with (
            override_settings(API_VERSIONING={"VERSIONS": {"v1": {"deprecation_link": 123}}}),
            pytest.raises(ImproperlyConfigured, match="must be"),
        ):
            get_setting("VERSIONS")

    def test_sunset_before_deprecated_raises_improperly_configured(self) -> None:
        with (
            override_settings(
                API_VERSIONING={
                    "VERSIONS": {
                        "v1": {
                            "deprecated": datetime.date(2026, 6, 1),
                            "sunset": datetime.date(2026, 1, 1),
                        }
                    }
                }
            ),
            pytest.raises(ImproperlyConfigured, match="cannot be earlier"),
        ):
            get_setting("VERSIONS")

    def test_default_version_not_in_versions_raises_improperly_configured(self) -> None:
        with (
            override_settings(API_VERSIONING={"VERSIONS": {"v1": {}}, "DEFAULT_VERSION": "v2"}),
            pytest.raises(ImproperlyConfigured, match="must be a key"),
        ):
            get_setting("DEFAULT_VERSION")

    def test_default_version_none_is_allowed(self) -> None:
        with override_settings(API_VERSIONING={"VERSIONS": {"v1": {}}, "DEFAULT_VERSION": None}):
            assert get_setting("DEFAULT_VERSION") is None
