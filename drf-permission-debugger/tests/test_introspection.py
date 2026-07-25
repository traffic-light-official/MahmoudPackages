"""Tests for :mod:`drf_permission_debugger.introspection`."""

from __future__ import annotations

from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from drf_permission_debugger.introspection import describe_permissions, describe_view
from tests.test_app.permissions import DenyAll, IsOwner


class _RequestOnlyView(APIView):
    permission_classes = [AllowAny, IsAuthenticated]


class _ObjectLevelView(APIView):
    permission_classes = [IsAuthenticated, IsOwner]


class _NoPermissionsView(APIView):
    permission_classes = []


class _FullStackView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    throttle_classes = [AnonRateThrottle]


class TestDescribePermissions:
    def test_describes_every_configured_permission_in_order(self) -> None:
        descriptions = describe_permissions(_RequestOnlyView)
        assert [d.name for d in descriptions] == ["AllowAny", "IsAuthenticated"]

    def test_request_level_only_permission_is_not_flagged_object_level(self) -> None:
        descriptions = describe_permissions(_RequestOnlyView)
        assert all(not d.checks_object_permission for d in descriptions)

    def test_object_level_permission_is_flagged(self) -> None:
        descriptions = describe_permissions(_ObjectLevelView)
        by_name = {d.name: d for d in descriptions}
        assert by_name["IsOwner"].checks_object_permission is True
        assert by_name["IsAuthenticated"].checks_object_permission is False

    def test_class_with_no_own_docstring_gets_empty_string(self) -> None:
        # Deliberately subclasses IsAuthenticated, which *does* have its
        # own docstring - proving the result is "" (not IsAuthenticated's
        # inherited text) confirms describe_permissions() doesn't fall
        # back to an inherited docstring.
        class _Undocumented(IsAuthenticated):
            pass

        class _View(APIView):
            permission_classes = [_Undocumented]

        descriptions = describe_permissions(_View)
        assert descriptions[0].docstring == ""

    def test_no_permission_classes_returns_empty_list(self) -> None:
        assert describe_permissions(_NoPermissionsView) == []

    def test_deny_all_docstring_captured_directly(self) -> None:
        class _View(APIView):
            permission_classes = [DenyAll]

        descriptions = describe_permissions(_View)
        assert "Always denies" in descriptions[0].docstring


class TestDescribeView:
    def test_includes_all_three_stacks(self) -> None:
        description = describe_view(_FullStackView)
        assert [d.name for d in description["permissions"]] == ["IsAuthenticated"]
        assert description["authentication_classes"] == ["SessionAuthentication"]
        assert description["throttle_classes"] == ["AnonRateThrottle"]

    def test_unset_throttle_classes_defaults_to_empty(self) -> None:
        # APIView.throttle_classes itself defaults to [] (DEFAULT_THROTTLE_CLASSES
        # is empty out of the box) - unlike authentication_classes, which
        # APIView already defaults to [SessionAuthentication, BasicAuthentication].
        description = describe_view(_RequestOnlyView)
        assert description["throttle_classes"] == []

    def test_unset_authentication_classes_uses_apiviews_own_default(self) -> None:
        description = describe_view(_RequestOnlyView)
        assert description["authentication_classes"] == [
            "SessionAuthentication",
            "BasicAuthentication",
        ]
