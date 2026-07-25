"""Tests for :mod:`drf_api_reverse.naming`."""

from __future__ import annotations

import pytest

from drf_api_reverse.naming import (
    comment_safe,
    is_param_segment,
    path_segments,
    resource_group_key,
    serializer_class_name,
    to_class_name,
    to_snake_case,
    viewset_class_name,
)


class TestToClassName:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("blog_post", "BlogPost"),
            ("blog-post", "BlogPost"),
            ("BlogPost", "BlogPost"),
            ("blogPost", "BlogPost"),
            ("articles", "Articles"),
            ("", "Unnamed"),
        ],
    )
    def test_converts_every_identifier_style(self, raw: str, expected: str) -> None:
        assert to_class_name(raw) == expected

    def test_sanitizes_characters_that_are_not_alphanumeric(self) -> None:
        assert to_class_name('"; import os') == "ImportOs"


class TestToSnakeCase:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("BlogPost", "blog_post"),
            ("blog-post", "blog_post"),
            ("blog_post", "blog_post"),
            ("displayName", "display_name"),
            ("", "unnamed"),
        ],
    )
    def test_converts_every_identifier_style(self, raw: str, expected: str) -> None:
        assert to_snake_case(raw) == expected


class TestPathSegments:
    def test_splits_and_strips_slashes(self) -> None:
        assert path_segments("/articles/{id}/comments/") == ["articles", "{id}", "comments"]

    def test_handles_root_path(self) -> None:
        assert path_segments("/") == []


class TestIsParamSegment:
    def test_true_for_brace_wrapped_segment(self) -> None:
        assert is_param_segment("{id}") is True

    def test_false_for_literal_segment(self) -> None:
        assert is_param_segment("articles") is False


class TestResourceGroupKey:
    def test_groups_collection_and_detail_together(self) -> None:
        assert resource_group_key("/articles/") == "articles"
        assert resource_group_key("/articles/{id}/") == "articles"

    def test_groups_nested_subresource_with_parent(self) -> None:
        assert resource_group_key("/articles/{id}/comments/") == "articles"

    def test_root_only_path_falls_back(self) -> None:
        assert resource_group_key("/{id}/") == "root"


class TestClassNameHelpers:
    def test_viewset_class_name(self) -> None:
        assert viewset_class_name("articles") == "ArticlesViewSet"

    def test_serializer_class_name(self) -> None:
        assert serializer_class_name("Article") == "ArticleSerializer"


class TestCommentSafe:
    def test_passes_through_plain_text(self) -> None:
        assert comment_safe("GET /articles/") == "GET /articles/"

    def test_collapses_embedded_newlines(self) -> None:
        malicious = "articles\nimport os; os.system('rm -rf /')"
        result = comment_safe(malicious)
        assert "\n" not in result
        assert result == "articles import os; os.system('rm -rf /')"
