"""Unit tests for naming helpers."""

from __future__ import annotations

from drf_llm_gateway.naming import viewset_base_name


class TestViewsetBaseName:
    def test_strips_viewset_suffix(self) -> None:
        class ArticleViewSet:
            pass

        assert viewset_base_name(ArticleViewSet) == "article"

    def test_strips_apiview_suffix(self) -> None:
        class ArticleAPIView:
            pass

        assert viewset_base_name(ArticleAPIView) == "article"

    def test_strips_view_suffix(self) -> None:
        class ArticleView:
            pass

        assert viewset_base_name(ArticleView) == "article"

    def test_camel_case_multi_word(self) -> None:
        class BlogArticleCommentViewSet:
            pass

        assert viewset_base_name(BlogArticleCommentViewSet) == "blog_article_comment"

    def test_no_suffix_is_unchanged_but_lowercased(self) -> None:
        class Article:
            pass

        assert viewset_base_name(Article) == "article"

    def test_name_exactly_matching_suffix_is_not_stripped_to_empty(self) -> None:
        class ViewSet:
            pass

        assert viewset_base_name(ViewSet) == "view_set"
