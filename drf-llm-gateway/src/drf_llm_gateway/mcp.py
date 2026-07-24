"""Export registered tools in Model Context Protocol (MCP) tool format.

See https://modelcontextprotocol.io/docs/concepts/tools for the target
schema shape: a list of ``{"name": ..., "description": ..., "inputSchema":
...}`` objects suitable for an MCP server's ``tools/list`` response.
"""

from __future__ import annotations

from typing import Any

from drf_llm_gateway.registry import ToolDefinition, ToolRegistry, default_registry


def to_mcp_tool(tool: ToolDefinition) -> dict[str, Any]:
    """Convert a single :class:`ToolDefinition` to an MCP tool object.

    Args:
        tool: The tool definition to convert.

    Returns:
        A ``dict`` of the form ``{"name": ..., "description": ...,
        "inputSchema": ...}``, matching the shape an MCP server returns
        from ``tools/list`` and expects to receive lookups against from
        ``tools/call``.
    """
    return {
        "name": tool.name,
        "description": tool.description,
        "inputSchema": tool.input_json_schema(),
    }


def to_mcp_tools(registry: ToolRegistry | None = None) -> list[dict[str, Any]]:
    """Convert every tool in a registry to MCP tool objects.

    Args:
        registry: The registry to export. Defaults to
            :data:`drf_llm_gateway.registry.default_registry`.

    Returns:
        A list of MCP tool objects, in registration order — directly
        usable as the ``tools`` array of a ``tools/list`` response.
    """
    source = registry if registry is not None else default_registry
    return [to_mcp_tool(tool) for tool in source]
