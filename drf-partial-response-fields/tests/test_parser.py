"""Unit tests for the ``fields`` mini-language parser."""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from drf_partial_response_fields.exceptions import InvalidFieldsParameterError
from drf_partial_response_fields.parser import parse_fields
from drf_partial_response_fields.tree import ALL_TREE


class TestBasicParsing:
    def test_empty_string_means_all(self) -> None:
        assert parse_fields("") is ALL_TREE

    def test_single_field(self) -> None:
        tree = parse_fields("id")
        assert tree.mode == "include"
        assert set(tree.includes) == {"id"}

    def test_multiple_fields(self) -> None:
        tree = parse_fields("id,name,email")
        assert tree.mode == "include"
        assert set(tree.includes) == {"id", "name", "email"}

    def test_whitespace_is_ignored(self) -> None:
        tree = parse_fields(" id , name ")
        assert set(tree.includes) == {"id", "name"}

    def test_trailing_and_leading_commas_are_tolerated(self) -> None:
        tree = parse_fields(",id,,name,")
        assert set(tree.includes) == {"id", "name"}

    def test_star_means_all(self) -> None:
        assert parse_fields("*") is ALL_TREE

    def test_underscore_and_digits_in_name(self) -> None:
        tree = parse_fields("_private,field_2")
        assert set(tree.includes) == {"_private", "field_2"}


class TestNestedParsing:
    def test_single_level_nesting(self) -> None:
        tree = parse_fields("author(name,email)")
        assert tree.mode == "include"
        author_spec = tree.includes["author"]
        assert author_spec.children is not None
        assert set(author_spec.children.includes) == {"name", "email"}

    def test_deep_nesting(self) -> None:
        tree = parse_fields("a(b(c(d)))", max_depth=10)
        node = tree.includes["a"].children
        assert node is not None
        node = node.includes["b"].children
        assert node is not None
        node = node.includes["c"].children
        assert node is not None
        assert set(node.includes) == {"d"}

    def test_field_without_parens_has_no_child_restriction(self) -> None:
        tree = parse_fields("author,title")
        assert tree.includes["author"].children is None

    def test_multiple_nested_groups_at_same_level(self) -> None:
        tree = parse_fields("author(name),editor(name)")
        assert set(tree.includes["author"].children.includes) == {"name"}  # type: ignore[union-attr]
        assert set(tree.includes["editor"].children.includes) == {"name"}  # type: ignore[union-attr]

    def test_sibling_fields_alongside_nested(self) -> None:
        tree = parse_fields("title,author(name)")
        assert set(tree.includes) == {"title", "author"}


class TestExclusion:
    def test_single_exclusion(self) -> None:
        tree = parse_fields("-password")
        assert tree.mode == "exclude"
        assert tree.excludes == frozenset({"password"})

    def test_multiple_exclusions(self) -> None:
        tree = parse_fields("-password,-internal_notes")
        assert tree.excludes == frozenset({"password", "internal_notes"})

    def test_mixing_include_and_exclude_is_rejected(self) -> None:
        with pytest.raises(InvalidFieldsParameterError):
            parse_fields("id,-password")


class TestAliasing:
    def test_simple_alias(self) -> None:
        tree = parse_fields("publishedAt:created_at")
        spec = tree.includes["created_at"]
        assert spec.alias == "publishedAt"

    def test_aliased_nested_field(self) -> None:
        tree = parse_fields("writer:author(name)")
        spec = tree.includes["author"]
        assert spec.alias == "writer"
        assert set(spec.children.includes) == {"name"}  # type: ignore[union-attr]


class TestWildcardRules:
    def test_star_alone_is_all(self) -> None:
        assert parse_fields("*") is ALL_TREE

    def test_star_combined_with_name_is_rejected(self) -> None:
        with pytest.raises(InvalidFieldsParameterError):
            parse_fields("*,id")

    def test_star_combined_with_exclusion_is_rejected(self) -> None:
        with pytest.raises(InvalidFieldsParameterError):
            parse_fields("*,-id")

    def test_nested_star_is_all_for_that_level(self) -> None:
        tree = parse_fields("author(*)")
        children = tree.includes["author"].children
        assert children is ALL_TREE


class TestFailureCases:
    @pytest.mark.parametrize(
        "raw",
        [
            "author(name",  # unbalanced open paren
            "author(name))",  # extra close paren
            "author)",  # stray close paren
            "1field",  # name cannot start with a digit
            "field name",  # space inside an identifier position
            "field$",  # invalid character
            "-",  # dash with no name
            ":name",  # alias marker with no alias name
            "author(",  # empty but unterminated group
        ],
    )
    def test_invalid_syntax_raises(self, raw: str) -> None:
        with pytest.raises(InvalidFieldsParameterError):
            parse_fields(raw)

    def test_duplicate_include_raises(self) -> None:
        with pytest.raises(InvalidFieldsParameterError):
            parse_fields("id,id")

    def test_duplicate_exclude_raises(self) -> None:
        with pytest.raises(InvalidFieldsParameterError):
            parse_fields("-id,-id")

    def test_exceeding_max_length_raises(self) -> None:
        with pytest.raises(InvalidFieldsParameterError):
            parse_fields("a" * 10, max_length=5)

    def test_exceeding_max_depth_raises(self) -> None:
        with pytest.raises(InvalidFieldsParameterError):
            parse_fields("a(b(c(d)))", max_depth=2)

    def test_max_depth_boundary_is_accepted(self) -> None:
        # depth counts the top level as 1, so "a(b)" is depth 2.
        tree = parse_fields("a(b)", max_depth=2)
        assert tree.includes["a"].children is not None


class TestPropertyBased:
    @given(
        st.lists(
            st.from_regex(r"[A-Za-z_][A-Za-z0-9_]{0,20}", fullmatch=True),
            min_size=1,
            max_size=8,
            unique=True,
        )
    )
    def test_flat_include_list_round_trips_names(self, names: list[str]) -> None:
        raw = ",".join(names)
        tree = parse_fields(raw, max_length=10_000)
        assert tree.mode == "include"
        assert set(tree.includes) == set(names)

    @given(
        st.lists(
            st.from_regex(r"[A-Za-z_][A-Za-z0-9_]{0,20}", fullmatch=True),
            min_size=1,
            max_size=8,
            unique=True,
        )
    )
    def test_flat_exclude_list_round_trips_names(self, names: list[str]) -> None:
        raw = ",".join(f"-{n}" for n in names)
        tree = parse_fields(raw, max_length=10_000)
        assert tree.mode == "exclude"
        assert tree.excludes == frozenset(names)

    @pytest.mark.parametrize(
        "raw",
        ["(((((", ")))))", "((()))", "a" + ")" * 50, "(" * 50 + "a"],
    )
    def test_parser_never_infinite_loops_on_arbitrary_garbage(self, raw: str) -> None:
        with pytest.raises(InvalidFieldsParameterError):
            parse_fields(raw, max_length=10_000)

    def test_comma_only_input_is_tolerated_as_no_restriction(self) -> None:
        # Consistent with leading/trailing comma tolerance: a group with no
        # real entries at all means "no restriction", same as an empty string.
        assert parse_fields(",,,,,", max_length=10_000) is ALL_TREE
