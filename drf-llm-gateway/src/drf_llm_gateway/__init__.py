"""Expose Django REST Framework serializers and viewsets as LLM tools.

The public API is intentionally small:

* :func:`~drf_llm_gateway.registry.expose_as_tool` — a class decorator that
  registers a viewset's actions as tools.
* :func:`~drf_llm_gateway.openai_tools.to_openai_tools` /
  :func:`~drf_llm_gateway.mcp.to_mcp_tools` — export the registry in the
  format your agent framework expects.
* :func:`~drf_llm_gateway.executor.execute_tool` — dispatch a tool call
  with real DRF authentication, permission, and validation behavior.

See ``docs/quickstart.md`` for a complete end-to-end example.
"""

from __future__ import annotations

from drf_llm_gateway.exceptions import (
    LLMGatewayError,
    SchemaGenerationError,
    ToolExecutionError,
    ToolNotFoundError,
    ToolPermissionDeniedError,
    ToolRegistrationError,
    ToolValidationError,
)
from drf_llm_gateway.executor import ToolResult, execute_tool
from drf_llm_gateway.mcp import to_mcp_tool, to_mcp_tools
from drf_llm_gateway.openai_tools import to_openai_tool, to_openai_tools
from drf_llm_gateway.registry import (
    STANDARD_ACTIONS,
    ToolDefinition,
    ToolRegistry,
    default_registry,
    expose_as_tool,
)
from drf_llm_gateway.schema import serializer_to_json_schema
from drf_llm_gateway.versioning import compute_schema_hash

__version__ = "1.0.0"

__all__ = [
    "STANDARD_ACTIONS",
    "LLMGatewayError",
    "SchemaGenerationError",
    "ToolDefinition",
    "ToolExecutionError",
    "ToolNotFoundError",
    "ToolPermissionDeniedError",
    "ToolRegistrationError",
    "ToolRegistry",
    "ToolResult",
    "ToolValidationError",
    "__version__",
    "compute_schema_hash",
    "default_registry",
    "execute_tool",
    "expose_as_tool",
    "serializer_to_json_schema",
    "to_mcp_tool",
    "to_mcp_tools",
    "to_openai_tool",
    "to_openai_tools",
]
