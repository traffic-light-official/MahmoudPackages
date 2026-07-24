"""Export registered tools in OpenAI function-calling format.

See https://platform.openai.com/docs/guides/function-calling for the
target schema shape: a list of ``{"type": "function", "function": {...}}``
objects suitable for the ``tools`` parameter of a Chat Completions or
Responses API call.
"""

from __future__ import annotations

from typing import Any

from drf_llm_gateway.registry import ToolDefinition, ToolRegistry, default_registry


def to_openai_tool(tool: ToolDefinition) -> dict[str, Any]:
    """Convert a single :class:`ToolDefinition` to an OpenAI tool object.

    Args:
        tool: The tool definition to convert.

    Returns:
        A dict shaped like the following, ready to pass directly in an
        OpenAI API call's ``tools`` argument:

        ```python
        {"type": "function", "function": {"name": ..., "description": ..., "parameters": ...}}
        ```
    """
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.input_json_schema(),
        },
    }


def to_openai_tools(registry: ToolRegistry | None = None) -> list[dict[str, Any]]:
    """Convert every tool in a registry to OpenAI tool objects.

    Args:
        registry: The registry to export. Defaults to
            :data:`drf_llm_gateway.registry.default_registry`.

    Returns:
        A list of OpenAI tool objects, in registration order.
    """
    source = registry if registry is not None else default_registry
    return [to_openai_tool(tool) for tool in source]
