"""Tests for :mod:`drf_async.permissions`."""

from __future__ import annotations

from rest_framework.permissions import BasePermission

from drf_async.permissions import BaseAsyncPermission, check_object_permission, check_permission


class TestBaseAsyncPermissionDefaults:
    async def test_has_permission_defaults_to_true(self) -> None:
        permission = BaseAsyncPermission()
        assert await permission.has_permission(request=object(), view=object()) is True

    async def test_has_object_permission_defaults_to_true(self) -> None:
        permission = BaseAsyncPermission()
        assert (
            await permission.has_object_permission(request=object(), view=object(), obj=object())
            is True
        )


class _SyncDeny(BasePermission):
    def has_permission(self, request: object, view: object) -> bool:
        return False

    def has_object_permission(self, request: object, view: object, obj: object) -> bool:
        return False


class _SyncAllow(BasePermission):
    pass  # BasePermission's own defaults already return True for both checks


class _AsyncDeny(BaseAsyncPermission):
    async def has_permission(self, request: object, view: object) -> bool:
        return False

    async def has_object_permission(self, request: object, view: object, obj: object) -> bool:
        return False


class TestCheckPermission:
    async def test_bridges_a_denying_sync_permission(self) -> None:
        assert await check_permission(_SyncDeny(), request=object(), view=object()) is False

    async def test_bridges_an_allowing_sync_permission(self) -> None:
        assert await check_permission(_SyncAllow(), request=object(), view=object()) is True

    async def test_awaits_a_denying_async_permission(self) -> None:
        assert await check_permission(_AsyncDeny(), request=object(), view=object()) is False


class TestCheckObjectPermission:
    async def test_bridges_a_denying_sync_permission(self) -> None:
        result = await check_object_permission(
            _SyncDeny(), request=object(), view=object(), obj=object()
        )
        assert result is False

    async def test_bridges_an_allowing_sync_permission(self) -> None:
        result = await check_object_permission(
            _SyncAllow(), request=object(), view=object(), obj=object()
        )
        assert result is True

    async def test_awaits_a_denying_async_permission(self) -> None:
        result = await check_object_permission(
            _AsyncDeny(), request=object(), view=object(), obj=object()
        )
        assert result is False
