"""Tests for drf_multitenant.settings."""

from __future__ import annotations

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from drf_multitenant.settings import get_setting


class TestDefaults:
    def test_tenant_field_defaults_to_tenant(self) -> None:
        assert get_setting("TENANT_FIELD") == "tenant"

    def test_strict_defaults_to_true(self) -> None:
        assert get_setting("STRICT") is True

    def test_resolver_defaults_to_header_resolver(self) -> None:
        assert get_setting("RESOLVER") == "drf_multitenant.resolvers.header_resolver"

    def test_tenant_model_is_configured_by_test_settings(self) -> None:
        assert get_setting("TENANT_MODEL") == "test_app.Tenant"

    def test_invalid_key_raises_key_error(self) -> None:
        with pytest.raises(KeyError):
            get_setting("NOT_A_REAL_SETTING")


class TestOverrides:
    def test_override_is_picked_up(self) -> None:
        with override_settings(MULTITENANT={"TENANT_FIELD": "organization"}):
            assert get_setting("TENANT_FIELD") == "organization"
        assert get_setting("TENANT_FIELD") == "tenant"

    def test_non_dict_setting_raises(self) -> None:
        with (
            override_settings(MULTITENANT="not-a-dict"),
            pytest.raises(ImproperlyConfigured, match="must be a dict"),
        ):
            get_setting("TENANT_FIELD")

    def test_unknown_key_raises(self) -> None:
        with (
            override_settings(MULTITENANT={"NOT_REAL": 1}),
            pytest.raises(ImproperlyConfigured, match="Unknown key"),
        ):
            get_setting("TENANT_FIELD")

    def test_wrong_type_raises(self) -> None:
        with (
            override_settings(MULTITENANT={"STRICT": "yes"}),
            pytest.raises(ImproperlyConfigured, match="must be of type"),
        ):
            get_setting("STRICT")

    def test_empty_tenant_field_raises(self) -> None:
        with (
            override_settings(MULTITENANT={"TENANT_FIELD": ""}),
            pytest.raises(ImproperlyConfigured, match="must not be empty"),
        ):
            get_setting("TENANT_FIELD")
