"""Tests for the ``list_api_versions`` management command."""

from __future__ import annotations

from io import StringIO

from django.core.management import call_command


def _run(*args: str) -> str:
    out = StringIO()
    call_command("list_api_versions", *args, stdout=out)
    return out.getvalue()


class TestListApiVersions:
    def test_lists_every_declared_version(self) -> None:
        output = _run()
        assert "v1:" in output
        assert "v2:" in output
        assert "v3 (default):" in output

    def test_marks_the_default_version(self) -> None:
        output = _run()
        assert "v3 (default):" in output
        assert "v1 (default)" not in output

    def test_v1_is_reported_as_sunset(self) -> None:
        output = _run()
        v1_line = next(line for line in output.splitlines() if line.startswith("v1"))
        assert "sunset" in v1_line
        assert "deprecated 2020-01-01" in v1_line
        assert "sunset 2020-06-01" in v1_line
        assert "https://example.com/docs/migrating-to-v3" in v1_line

    def test_v2_is_reported_as_deprecated_not_sunset(self) -> None:
        output = _run()
        v2_line = next(line for line in output.splitlines() if line.startswith("v2"))
        assert ": deprecated" in v2_line
        assert "sunset" not in v2_line.split(":")[1]

    def test_v3_is_reported_as_supported(self) -> None:
        output = _run()
        v3_line = next(line for line in output.splitlines() if line.startswith("v3"))
        assert "supported" in v3_line

    def test_status_filter_only_lists_matching_versions(self) -> None:
        output = _run("--status", "sunset")
        assert "v1:" in output
        assert "v2:" not in output
        assert "v3:" not in output

    def test_status_filter_supported(self) -> None:
        output = _run("--status", "supported")
        assert output.strip() == "v3 (default): supported"
