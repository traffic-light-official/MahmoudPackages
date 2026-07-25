"""Tests for :mod:`drf_api_reverse.regions`."""

from __future__ import annotations

import pytest

from drf_api_reverse.exceptions import RegionMergeError
from drf_api_reverse.regions import begin_marker, end_marker, existing_region_keys, merge


def _wrap(key: str, body: str) -> str:
    return f"{begin_marker(key)}\n{body}\n{end_marker(key)}"


class TestExistingRegionKeys:
    def test_finds_every_region_key(self) -> None:
        text = f"{_wrap('a', 'x = 1')}\n\n{_wrap('b', 'y = 2')}\n"
        assert existing_region_keys(text) == {"a", "b"}

    def test_empty_for_a_file_with_no_regions(self) -> None:
        assert existing_region_keys("just some plain code\n") == set()

    def test_raises_on_unmatched_begin_marker(self) -> None:
        with pytest.raises(RegionMergeError, match="no matching END"):
            existing_region_keys(f"{begin_marker('a')}\nx = 1\n")

    def test_raises_on_mismatched_end_key(self) -> None:
        with pytest.raises(RegionMergeError, match="closed by END marker"):
            existing_region_keys(f"{begin_marker('a')}\nx = 1\n{end_marker('b')}\n")

    def test_raises_on_duplicate_keys(self) -> None:
        text = f"{_wrap('a', 'x = 1')}\n{_wrap('a', 'x = 2')}\n"
        with pytest.raises(RegionMergeError, match="Duplicate"):
            existing_region_keys(text)


class TestMergeBrandNewRegions:
    def test_appends_regions_not_previously_present(self) -> None:
        existing = "# a hand-written header\nimport os\n"
        new_text, orphaned = merge(existing, {"a": "class A: pass"})

        assert "# a hand-written header" in new_text
        assert "import os" in new_text
        assert _wrap("a", "class A: pass") in new_text
        assert orphaned == []

    def test_appended_regions_preserve_generation_order(self) -> None:
        new_text, _ = merge("", {"a": "x = 1", "b": "y = 2"})
        assert new_text.index("x = 1") < new_text.index("y = 2")


class TestMergeUpdatesExistingRegions:
    def test_replaces_only_the_region_body(self) -> None:
        existing = f"import os\n\n{_wrap('a', 'x = 1')}\n\nmy_custom_code()\n"
        new_text, orphaned = merge(existing, {"a": "x = 2"})

        assert "import os" in new_text
        assert "my_custom_code()" in new_text
        assert _wrap("a", "x = 2") in new_text
        assert "x = 1" not in new_text
        assert orphaned == []

    def test_custom_code_between_regions_survives(self) -> None:
        existing = f"{_wrap('a', 'x = 1')}\n\n# custom glue\n\n{_wrap('b', 'y = 1')}\n"
        new_text, _ = merge(existing, {"a": "x = 2", "b": "y = 2"})

        assert "# custom glue" in new_text
        assert _wrap("a", "x = 2") in new_text
        assert _wrap("b", "y = 2") in new_text


class TestMergeOrphanedRegions:
    def test_region_no_longer_in_generated_set_is_reported_but_kept(self) -> None:
        existing = _wrap("a", "x = 1")
        new_text, orphaned = merge(existing, {})

        assert orphaned == ["a"]
        assert _wrap("a", "x = 1") in new_text

    def test_orphaned_region_body_is_never_modified(self) -> None:
        existing = f"{_wrap('a', 'x = 1')}\n\n{_wrap('b', 'y = 1')}\n"
        new_text, orphaned = merge(existing, {"a": "x = 2"})

        assert orphaned == ["b"]
        assert _wrap("b", "y = 1") in new_text
        assert _wrap("a", "x = 2") in new_text


class TestMergeErrors:
    def test_raises_on_malformed_existing_file(self) -> None:
        with pytest.raises(RegionMergeError):
            merge(f"{begin_marker('a')}\nx = 1\n", {"a": "x = 2"})


class TestMergeRoundTrip:
    def test_regenerating_twice_with_the_same_input_is_stable(self) -> None:
        first, _ = merge("", {"a": "x = 1", "b": "y = 1"})
        second, orphaned = merge(first, {"a": "x = 1", "b": "y = 1"})

        assert second == first
        assert orphaned == []
