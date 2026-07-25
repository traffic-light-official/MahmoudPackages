"""Tests for the ``show_view_permissions`` management command."""

from __future__ import annotations

import io

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError


class TestShowViewPermissions:
    def test_prints_the_resolved_view_and_its_permission_stack(self) -> None:
        out = io.StringIO()
        call_command("show_view_permissions", "/multi-denied/", stdout=out)
        output = out.getvalue()
        assert "MultiPermissionDeniedView" in output
        assert "IsAuthenticated" in output
        assert "DenyAll" in output
        assert "Denied by DenyAll" in output or "Always denies" in output

    def test_prints_object_level_marker_for_object_level_permissions(self) -> None:
        out = io.StringIO()
        call_command("show_view_permissions", "/articles/1/", stdout=out)
        output = out.getvalue()
        assert "IsOwner [object-level]" in output
        assert "IsAuthenticated\n" in output or "IsAuthenticated " in output

    def test_prints_authentication_and_throttle_sections(self) -> None:
        out = io.StringIO()
        call_command("show_view_permissions", "/ping/", stdout=out)
        output = out.getvalue()
        assert "authentication_classes" in output
        assert "throttle_classes" in output

    def test_unresolvable_path_raises_command_error(self) -> None:
        with pytest.raises(CommandError, match="No URL matches"):
            call_command("show_view_permissions", "/does-not-exist/")

    def test_plain_function_view_raises_command_error(self) -> None:
        with pytest.raises(CommandError, match="does not resolve to a class-based view"):
            call_command("show_view_permissions", "/function-view/")

    def test_no_permissions_prints_none_for_permissions_and_authentication(self) -> None:
        out = io.StringIO()
        call_command("show_view_permissions", "/no-permissions/", stdout=out)
        output = out.getvalue()
        assert "permission_classes (0):" in output
        assert "authentication_classes (0):" in output
        assert output.count("(none)") == 2

    def test_no_permissions_prints_its_one_throttle_class(self) -> None:
        out = io.StringIO()
        call_command("show_view_permissions", "/no-permissions/", stdout=out)
        output = out.getvalue()
        assert "throttle_classes (1):" in output
        assert "- AnonRateThrottle" in output

    def test_undocumented_permission_prints_no_description_line(self) -> None:
        out = io.StringIO()
        call_command("show_view_permissions", "/undocumented-permission/", stdout=out)
        output = out.getvalue()
        assert "- Undocumented" in output
        lines = output.splitlines()
        undocumented_index = next(i for i, line in enumerate(lines) if "- Undocumented" in line)
        # The next line is a new section header, not an indented description.
        assert not lines[undocumented_index + 1].startswith("      ")
