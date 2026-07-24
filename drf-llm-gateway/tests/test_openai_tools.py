"""Tests for the OpenAI function-calling export."""

from __future__ import annotations

import pytest
from rest_framework import viewsets

from drf_llm_gateway.openai_tools import to_openai_tool, to_openai_tools
from drf_llm_gateway.registry import ToolRegistry, expose_as_tool
from tests.test_app.models import Article
from tests.test_app.serializers import ArticleSerializer

pytestmark = pytest.mark.django_db


@pytest.fixture
def sample_registry() -> ToolRegistry:
    registry = ToolRegistry()

    @expose_as_tool(actions=["list", "retrieve"], registry=registry)
    class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
        queryset = Article.objects.all()
        serializer_class = ArticleSerializer

    return registry


class TestToOpenAiTool:
    def test_shape(self, sample_registry: ToolRegistry) -> None:
        tool = sample_registry.get("article_list")
        openai_tool = to_openai_tool(tool)
        assert openai_tool["type"] == "function"
        assert openai_tool["function"]["name"] == "article_list"
        assert openai_tool["function"]["description"] == "List Article objects."
        assert openai_tool["function"]["parameters"]["type"] == "object"

    def test_retrieve_has_lookup_parameter(self, sample_registry: ToolRegistry) -> None:
        tool = sample_registry.get("article_retrieve")
        openai_tool = to_openai_tool(tool)
        params = openai_tool["function"]["parameters"]
        assert params["properties"]["pk"] == {"type": "integer"}
        assert params["required"] == ["pk"]


class TestToOpenAiTools:
    def test_exports_every_tool(self, sample_registry: ToolRegistry) -> None:
        tools = to_openai_tools(sample_registry)
        names = {t["function"]["name"] for t in tools}
        assert names == {"article_list", "article_retrieve"}

    def test_empty_registry_returns_empty_list(self) -> None:
        assert to_openai_tools(ToolRegistry()) == []
