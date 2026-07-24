# drf-llm-gateway

Turn your existing Django REST Framework viewsets into tools an LLM can
call — OpenAI function-calling format, MCP (Model Context Protocol) tool
format, or plain JSON Schema — generated automatically from the
serializers you already have.

## Why this exists

Wiring an LLM agent to call your API usually means hand-writing a parallel
set of tool/function schemas that drift out of sync with your serializers
the moment either side changes. This package derives the schema *from the
serializer itself* every time it's generated — there's nothing to keep in
sync.

```python
from rest_framework import viewsets
from drf_llm_gateway import expose_as_tool


@expose_as_tool(actions=["list", "retrieve", "create"])
class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
```

```python
from drf_llm_gateway import to_openai_tools, execute_tool

tools = to_openai_tools()  # ready for an OpenAI API call's `tools=` argument
result = execute_tool("article_create", {"title": "Hello", "author": 1}, user=request.user)
```

## Where to go next

- New to the package? Start with [Getting Started](getting-started.md).
- Wiring it into an existing project? See [Installation](installation.md)
  and [Configuration](configuration.md).
- Want the full picture? Read [Architecture](architecture.md).
- Looking for a specific class or setting? Jump to
  [API Reference](api-reference.md) or [Settings](settings.md).
- Something not behaving as expected? Check [Troubleshooting](troubleshooting.md).

## At a glance

| Task | Where |
| --- | --- |
| Register a viewset's actions as tools | [`expose_as_tool`](api-reference.md#expose_as_tool) |
| Export for OpenAI function calling | [`to_openai_tools`](api-reference.md#to_openai_tools) |
| Export for an MCP server | [`to_mcp_tools`](api-reference.md#to_mcp_tools) |
| Dispatch a tool call at runtime | [`execute_tool`](api-reference.md#execute_tool) |
| Convert any serializer to JSON Schema | [`serializer_to_json_schema`](api-reference.md#serializer_to_json_schema) |
| Optimize a `SerializerMethodField`-style computed tool | see [Advanced Usage](advanced-usage.md) |
| Export tools from the command line | `python manage.py generate_llm_tools` |
