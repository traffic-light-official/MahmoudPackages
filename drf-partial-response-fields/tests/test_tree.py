"""Unit tests for the tree data structures and resolution helpers."""

from __future__ import annotations

import pytest

from drf_partial_response_fields.exceptions import UnknownFieldError
from drf_partial_response_fields.parser import parse_fields
from drf_partial_response_fields.tree import ALL_TREE, child_tree, resolve_allowed_names


class TestResolveAllowedNames:
    def test_all_mode_returns_everything_available(self) -> None:
        assert resolve_allowed_names(ALL_TREE, {"a", "b", "c"}, strict=False) == {"a", "b", "c"}

    def test_include_mode_returns_intersection(self) -> None:
        tree = parse_fields("a,b")
        assert resolve_allowed_names(tree, {"a", "b", "c"}, strict=False) == {"a", "b"}

    def test_include_mode_silently_drops_unknown_when_not_strict(self) -> None:
        tree = parse_fields("a,zzz")
        assert resolve_allowed_names(tree, {"a", "b"}, strict=False) == {"a"}

    def test_include_mode_raises_on_unknown_when_strict(self) -> None:
        tree = parse_fields("a,zzz")
        with pytest.raises(UnknownFieldError):
            resolve_allowed_names(tree, {"a", "b"}, strict=True)

    def test_exclude_mode_returns_complement(self) -> None:
        tree = parse_fields("-a")
        assert resolve_allowed_names(tree, {"a", "b", "c"}, strict=False) == {"b", "c"}

    def test_exclude_mode_unknown_name_is_a_no_op_when_not_strict(self) -> None:
        tree = parse_fields("-zzz")
        assert resolve_allowed_names(tree, {"a", "b"}, strict=False) == {"a", "b"}

    def test_exclude_mode_raises_on_unknown_when_strict(self) -> None:
        tree = parse_fields("-zzz")
        with pytest.raises(UnknownFieldError):
            resolve_allowed_names(tree, {"a", "b"}, strict=True)


class TestChildTree:
    def test_all_tree_has_all_children(self) -> None:
        assert child_tree(ALL_TREE, "anything") is ALL_TREE

    def test_exclude_tree_never_restricts_children(self) -> None:
        tree = parse_fields("-a")
        assert child_tree(tree, "b") is ALL_TREE

    def test_include_without_nested_group_is_unrestricted(self) -> None:
        tree = parse_fields("author")
        assert child_tree(tree, "author") is ALL_TREE

    def test_include_with_nested_group_returns_it(self) -> None:
        tree = parse_fields("author(name)")
        nested = child_tree(tree, "author")
        assert nested.mode == "include"
        assert set(nested.includes) == {"name"}

    def test_unrequested_field_name_is_all(self) -> None:
        tree = parse_fields("author(name)")
        assert child_tree(tree, "editor") is ALL_TREE
