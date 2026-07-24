"""Tests for drf_multitenant.context."""

from __future__ import annotations

import pytest

from drf_multitenant.context import (
    get_current_tenant,
    require_current_tenant,
    reset_current_tenant,
    set_current_tenant,
    tenant_context,
)
from drf_multitenant.exceptions import NoTenantSetError


class TestGetCurrentTenant:
    def test_defaults_to_none(self) -> None:
        assert get_current_tenant() is None

    def test_reflects_set_value(self) -> None:
        token = set_current_tenant("tenant-1")
        try:
            assert get_current_tenant() == "tenant-1"
        finally:
            reset_current_tenant(token)


class TestRequireCurrentTenant:
    def test_raises_when_unset(self) -> None:
        with pytest.raises(NoTenantSetError):
            require_current_tenant()

    def test_returns_tenant_when_set(self) -> None:
        with tenant_context("tenant-1"):
            assert require_current_tenant() == "tenant-1"


class TestTenantContext:
    def test_sets_and_restores(self) -> None:
        assert get_current_tenant() is None
        with tenant_context("tenant-1"):
            assert get_current_tenant() == "tenant-1"
        assert get_current_tenant() is None

    def test_restores_on_exception(self) -> None:
        with pytest.raises(ValueError, match="boom"), tenant_context("tenant-1"):
            raise ValueError("boom")
        assert get_current_tenant() is None

    def test_nested_contexts_restore_outer_value(self) -> None:
        with tenant_context("outer"):
            with tenant_context("inner"):
                assert get_current_tenant() == "inner"
            assert get_current_tenant() == "outer"
        assert get_current_tenant() is None

    def test_none_explicitly_clears(self) -> None:
        with tenant_context("tenant-1"):
            with tenant_context(None):
                assert get_current_tenant() is None
            assert get_current_tenant() == "tenant-1"


class TestSetResetCurrentTenant:
    def test_manual_set_and_reset(self) -> None:
        token = set_current_tenant("tenant-1")
        assert get_current_tenant() == "tenant-1"
        reset_current_tenant(token)
        assert get_current_tenant() is None
