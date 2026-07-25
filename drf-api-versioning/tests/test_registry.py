"""Tests for :mod:`drf_api_versioning.registry`."""

from __future__ import annotations

import datetime

import pytest
from django.test import override_settings

from drf_api_versioning import registry


class TestAllVersionNames:
    def test_matches_test_settings(self) -> None:
        assert registry.all_version_names() == ("v1", "v2", "v3")


class TestGetVersionInfo:
    def test_v1_has_deprecated_and_sunset(self) -> None:
        info = registry.get_version_info("v1")
        assert info.deprecated_on == datetime.date(2020, 1, 1)
        assert info.sunset_on == datetime.date(2020, 6, 1)
        assert info.deprecation_link == "https://example.com/docs/migrating-to-v3"

    def test_v2_has_deprecated_but_no_sunset(self) -> None:
        info = registry.get_version_info("v2")
        assert info.deprecated_on == datetime.date(2020, 1, 1)
        assert info.sunset_on is None
        assert info.deprecation_link is None

    def test_v3_has_neither(self) -> None:
        info = registry.get_version_info("v3")
        assert info.deprecated_on is None
        assert info.sunset_on is None

    def test_unknown_version_raises_key_error(self) -> None:
        with pytest.raises(KeyError):
            registry.get_version_info("v99")

    def test_datetime_value_is_normalized_to_date(self) -> None:
        with override_settings(
            API_VERSIONING={
                "VERSIONS": {"v1": {"deprecated": datetime.datetime(2026, 1, 1, 12, 30)}}
            }
        ):
            info = registry.get_version_info("v1")
        assert info.deprecated_on == datetime.date(2026, 1, 1)


class TestVersionInfoIsDeprecated:
    def test_past_deprecated_date_is_deprecated(self) -> None:
        info = registry.get_version_info("v1")
        assert info.is_deprecated() is True

    def test_no_deprecated_date_is_never_deprecated(self) -> None:
        info = registry.get_version_info("v3")
        assert info.is_deprecated() is False

    def test_explicit_as_of_before_deprecation_is_not_deprecated(self) -> None:
        info = registry.get_version_info("v1")
        assert info.is_deprecated(as_of=datetime.date(2019, 1, 1)) is False

    def test_explicit_as_of_on_the_deprecation_date_is_deprecated(self) -> None:
        info = registry.get_version_info("v1")
        assert info.is_deprecated(as_of=datetime.date(2020, 1, 1)) is True


class TestVersionInfoIsSunset:
    def test_past_sunset_date_is_sunset(self) -> None:
        info = registry.get_version_info("v1")
        assert info.is_sunset() is True

    def test_no_sunset_date_is_never_sunset(self) -> None:
        info = registry.get_version_info("v2")
        assert info.is_sunset() is False

    def test_explicit_as_of_before_sunset_is_not_sunset(self) -> None:
        info = registry.get_version_info("v1")
        assert info.is_sunset(as_of=datetime.date(2020, 5, 1)) is False


class TestAllVersions:
    def test_returns_one_entry_per_declared_version(self) -> None:
        versions = registry.all_versions()
        assert [v.name for v in versions] == ["v1", "v2", "v3"]


class TestDefaultVersionName:
    def test_matches_test_settings(self) -> None:
        assert registry.default_version_name() == "v3"

    def test_none_when_unset(self) -> None:
        with override_settings(API_VERSIONING={"VERSIONS": {"only": {}}, "DEFAULT_VERSION": None}):
            assert registry.default_version_name() is None
