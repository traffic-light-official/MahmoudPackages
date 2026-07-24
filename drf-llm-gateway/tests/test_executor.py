"""Tests for the runtime tool executor."""

from __future__ import annotations

import pytest

from drf_llm_gateway.exceptions import (
    ToolNotFoundError,
    ToolPermissionDeniedError,
    ToolValidationError,
)
from drf_llm_gateway.executor import ToolResult, execute_tool
from drf_llm_gateway.registry import default_registry
from tests.test_app.models import Article, Author

pytestmark = pytest.mark.django_db


class TestToolNotFound:
    def test_unregistered_tool_raises(self) -> None:
        with pytest.raises(ToolNotFoundError):
            execute_tool("does_not_exist", {})


class TestPermissionEnforcement:
    def test_anonymous_call_to_protected_tool_is_denied(self, article: Article) -> None:
        with pytest.raises(ToolPermissionDeniedError):
            execute_tool("article_list", {})

    def test_authenticated_call_succeeds(self, article: Article, user: object) -> None:
        result = execute_tool("article_list", {}, user=user)
        assert isinstance(result, ToolResult)
        assert result.status_code == 200

    def test_public_viewset_allows_anonymous(self, article: Article) -> None:
        Article.objects.filter(pk=article.pk).update(status=Article.Status.PUBLISHED)
        result = execute_tool("public_article_list", {})
        assert result.status_code == 200

    def test_enforce_permissions_disabled_bypasses_check(self, article: Article) -> None:
        from django.test import override_settings

        with override_settings(LLM_GATEWAY={"ENFORCE_PERMISSIONS": False}):
            result = execute_tool("article_list", {})
        assert result.status_code == 200


class TestCrudDispatch:
    def test_list_returns_articles(self, article: Article, user: object) -> None:
        result = execute_tool("article_list", {}, user=user)
        assert len(result.data) == 1
        assert result.data[0]["title"] == "Hello World"

    def test_retrieve_returns_single_article(self, article: Article, user: object) -> None:
        result = execute_tool("article_retrieve", {"pk": article.pk}, user=user)
        assert result.status_code == 200
        assert result.data["title"] == "Hello World"

    def test_retrieve_missing_lookup_field_raises_validation_error(self, user: object) -> None:
        with pytest.raises(ToolValidationError):
            execute_tool("article_retrieve", {}, user=user)

    def test_create_dispatches_to_real_viewset(self, author: Author, user: object) -> None:
        result = execute_tool(
            "article_create", {"title": "New Article", "author": author.pk}, user=user
        )
        assert result.status_code == 201
        assert result.data["title"] == "New Article"
        assert Article.objects.filter(title="New Article").exists()

    def test_create_with_invalid_data_raises_validation_error(self, user: object) -> None:
        with pytest.raises(ToolValidationError):
            execute_tool("article_create", {"title": ""}, user=user)  # missing required author

    def test_update_replaces_article(self, article: Article, author: Author, user: object) -> None:
        result = execute_tool(
            "article_update",
            {"pk": article.pk, "title": "Updated Title", "author": author.pk},
            user=user,
        )
        assert result.status_code == 200
        article.refresh_from_db()
        assert article.title == "Updated Title"

    def test_partial_update_changes_only_given_fields(self, article: Article, user: object) -> None:
        result = execute_tool(
            "article_partial_update", {"pk": article.pk, "title": "Patched"}, user=user
        )
        assert result.status_code == 200
        article.refresh_from_db()
        assert article.title == "Patched"
        assert article.author_id is not None  # untouched

    def test_destroy_removes_article(self, article: Article, user: object) -> None:
        result = execute_tool("article_destroy", {"pk": article.pk}, user=user)
        assert result.status_code == 204
        assert not Article.objects.filter(pk=article.pk).exists()

    def test_custom_action_dispatch(self, article: Article, user: object) -> None:
        result = execute_tool("article_publish", {"pk": article.pk}, user=user)
        assert result.status_code == 200
        article.refresh_from_db()
        assert article.status == Article.Status.PUBLISHED

    def test_nonexistent_object_returns_404_result_without_raising(self, user: object) -> None:
        result = execute_tool("article_retrieve", {"pk": 99999}, user=user)
        assert result.status_code == 404


class TestDefaultRegistryIsUsedByDefault:
    def test_execute_tool_without_explicit_registry_uses_default(
        self, article: Article, user: object
    ) -> None:
        assert default_registry.get("article_list") is not None
        result = execute_tool("article_list", {}, user=user)
        assert result.status_code == 200
