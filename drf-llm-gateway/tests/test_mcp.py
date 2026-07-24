"""Tests for the MCP tool-format export."""

from __future__ import annotations

import pytest
from rest_framework import viewsets

from drf_llm_gateway.mcp import to_mcp_tool, to_mcp_tools
from drf_llm_gateway.registry import ToolRegistry, expose_as_tool
from tests.test_app.models import Article
from tests.test_app.serializers import ArticleSerializer

pytestmark = pytest.mark.django_db


@pytest.fixture
def sample_registry() -> ToolRegistry:
    registry = ToolRegistry()

    @expose_as_tool(actions=["list", "create"], registry=registry)
    class ArticleViewSet(viewsets.ModelViewSet):
        queryset = Article.objects.all()
        serializer_class = ArticleSerializer

    return registry


class TestToMcpTool:
    def test_shape(self, sample_registry: ToolRegistry) -> None:
        tool = sample_registry.get("article_create")
        mcp_tool = to_mcp_tool(tool)
        assert mcp_tool["name"] == "article_create"
        assert mcp_tool["description"] == "Create a new Article."
        assert mcp_tool["inputSchema"]["type"] == "object"
        assert "title" in mcp_tool["inputSchema"]["properties"]


class TestToMcpTools:
    def test_exports_every_tool(self, sample_registry: ToolRegistry) -> None:
        names = {t["name"] for t in to_mcp_tools(sample_registry)}
        assert names == {"article_list", "article_create"}
