"""Unit/integration tests for the serializer mixin."""

from __future__ import annotations

import pytest
from django.test import override_settings

from drf_partial_response_fields.constants import CONTEXT_KEY
from drf_partial_response_fields.exceptions import UnknownFieldError
from drf_partial_response_fields.parser import parse_fields
from tests.test_app.models import Article
from tests.test_app.serializers import ArticleSerializer, AuthorSerializer

pytestmark = pytest.mark.django_db


def _serialize(instance: object, raw_fields: str, *, many: bool = False) -> dict | list:
    tree = parse_fields(raw_fields)
    serializer_cls = (
        ArticleSerializer if isinstance(instance, (Article, list)) else AuthorSerializer
    )
    serializer = serializer_cls(instance, many=many, context={CONTEXT_KEY: tree})
    return serializer.data


class TestFlatFiltering:
    def test_no_fields_param_returns_everything(self, article: Article) -> None:
        data = _serialize(article, "")
        assert set(data) == {
            "id",
            "title",
            "body",
            "author",
            "tags",
            "comments",
            "comment_count",
            "editor_note",
            "view_count",
        }

    def test_include_subset(self, article: Article) -> None:
        data = _serialize(article, "id,title")
        assert set(data) == {"id", "title"}

    def test_exclude_subset(self, article: Article) -> None:
        data = _serialize(article, "-body,-comments")
        assert "body" not in data
        assert "comments" not in data
        assert "title" in data

    def test_always_include_pk_even_when_not_requested(self, article: Article) -> None:
        data = _serialize(article, "title")
        assert "id" in data
        assert "title" in data
        assert "body" not in data


class TestNestedFiltering:
    def test_nested_selection(self, article: Article) -> None:
        data = _serialize(article, "title,author(name)")
        assert set(data) == {"title", "author", "id"}
        assert set(data["author"]) == {"name", "id"}

    def test_nested_many_selection(self, article: Article) -> None:
        data = _serialize(article, "title,tags(label)")
        for tag in data["tags"]:
            assert set(tag) == {"label", "id"}

    def test_deeply_nested_selection(self, article: Article, profile: object) -> None:
        data = _serialize(article, "author(profile(display_name))")
        assert set(data["author"]["profile"]) == {"display_name", "id"}

    def test_unrestricted_nested_field_returns_full_default(self, article: Article) -> None:
        data = _serialize(article, "author")
        assert set(data["author"]) == {"id", "name", "email", "bio", "profile"}


class TestAliasing:
    def test_top_level_alias(self, article: Article) -> None:
        data = _serialize(article, "headline:title")
        assert "headline" in data
        assert data["headline"] == article.title
        assert "title" not in data

    def test_nested_alias(self, article: Article) -> None:
        data = _serialize(article, "author(fullName:name)")
        assert data["author"]["fullName"] == article.author.name
        assert "name" not in data["author"]


class TestSerializerMethodFieldSkipping:
    def test_unrequested_method_field_is_not_invoked(
        self, article: Article, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _explode(self: ArticleSerializer, obj: Article) -> int:
            raise AssertionError("get_comment_count should not be called when unrequested")

        monkeypatch.setattr(ArticleSerializer, "get_comment_count", _explode)
        data = _serialize(article, "title")
        assert "comment_count" not in data

    def test_requested_method_field_is_computed(self, article: Article) -> None:
        data = _serialize(article, "comment_count")
        assert data["comment_count"] == 2


class TestStrictMode:
    def test_unknown_field_ignored_by_default(self, article: Article) -> None:
        data = _serialize(article, "title,does_not_exist")
        assert "does_not_exist" not in data
        assert "title" in data

    def test_unknown_field_raises_in_strict_mode(self, article: Article) -> None:
        with (
            override_settings(PARTIAL_RESPONSE_FIELDS={"STRICT": True}),
            pytest.raises(UnknownFieldError),
        ):
            _serialize(article, "title,does_not_exist")


class TestManySerialization:
    def test_filtering_applies_to_every_item_in_a_list(self, many_articles: list[Article]) -> None:
        data = _serialize(many_articles, "title", many=True)
        assert isinstance(data, list)
        for item in data:
            assert set(item) == {"id", "title"}
