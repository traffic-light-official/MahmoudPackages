# API Reference

Generated in part from source docstrings via
[mkdocstrings](https://mkdocstrings.github.io/).

## Registration

### expose_as_tool

::: drf_llm_gateway.registry.expose_as_tool

### ToolRegistry

::: drf_llm_gateway.registry.ToolRegistry

### ToolDefinition

::: drf_llm_gateway.registry.ToolDefinition

### default_registry

The module-level `ToolRegistry` instance `expose_as_tool` registers into
unless a different `registry=` is passed explicitly.

### STANDARD_ACTIONS

Mapping of standard `ModelViewSet` action names to `(http_method, detail)`
tuples, used internally to resolve HTTP method and detail-ness for actions
that aren't custom `@action`-decorated methods.

## Schema generation

### serializer_to_json_schema

::: drf_llm_gateway.schema.serializer_to_json_schema

## Export formats

### to_openai_tool

::: drf_llm_gateway.openai_tools.to_openai_tool

### to_openai_tools

::: drf_llm_gateway.openai_tools.to_openai_tools

### to_mcp_tool

::: drf_llm_gateway.mcp.to_mcp_tool

### to_mcp_tools

::: drf_llm_gateway.mcp.to_mcp_tools

## Execution

### execute_tool

::: drf_llm_gateway.executor.execute_tool

### ToolResult

::: drf_llm_gateway.executor.ToolResult

## Versioning

### compute_schema_hash

::: drf_llm_gateway.versioning.compute_schema_hash

## Exceptions

### LLMGatewayError

::: drf_llm_gateway.exceptions.LLMGatewayError

### SchemaGenerationError

::: drf_llm_gateway.exceptions.SchemaGenerationError

### ToolRegistrationError

::: drf_llm_gateway.exceptions.ToolRegistrationError

### ToolExecutionError

::: drf_llm_gateway.exceptions.ToolExecutionError

### ToolNotFoundError

::: drf_llm_gateway.exceptions.ToolNotFoundError

### ToolValidationError

::: drf_llm_gateway.exceptions.ToolValidationError

### ToolPermissionDeniedError

::: drf_llm_gateway.exceptions.ToolPermissionDeniedError

## Settings

### get_setting

::: drf_llm_gateway.settings.get_setting

See [Settings](settings.md) for the full list of recognized keys.

## Management command

### generate_llm_tools

```bash
python manage.py generate_llm_tools [--format {openai,mcp,jsonschema}] [--indent N] [--urlconf PATH]
```

See [Quick Start](quickstart.md#exporting-from-the-command-line).
