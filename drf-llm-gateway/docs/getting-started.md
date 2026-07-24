# Getting Started

## Prerequisites

- Python 3.10+, Django 4.2+, Django REST Framework 3.14+.

## 1. Install

```bash
pip install drf-llm-gateway
```

Add `"drf_llm_gateway"` to `INSTALLED_APPS` **only if** you want the
`generate_llm_tools` management command (Django discovers management
commands per app). Every other feature works without it.

```python
INSTALLED_APPS = [
    ...,
    "drf_llm_gateway",  # optional - only needed for the CLI
]
```

## 2. Register a viewset

```python
from rest_framework import viewsets
from drf_llm_gateway import expose_as_tool


@expose_as_tool(actions=["list", "retrieve", "create"])
class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
```

This registers three tools — `article_list`, `article_retrieve`,
`article_create` — into the module-level default registry, the moment
this module is imported (which happens naturally once a router imports it
in your `urls.py`).

## 3. Export the tools

```python
from drf_llm_gateway import to_openai_tools

tools = to_openai_tools()
```

```json
[
  {
    "type": "function",
    "function": {
      "name": "article_list",
      "description": "List Article objects.",
      "parameters": {"type": "object", "properties": {}}
    }
  },
  {
    "type": "function",
    "function": {
      "name": "article_retrieve",
      "description": "Retrieve a single Article by its identifier.",
      "parameters": {
        "type": "object",
        "properties": {"pk": {"type": "integer"}},
        "required": ["pk"]
      }
    }
  }
]
```

Pass `tools` directly as the `tools=` argument of an OpenAI Chat
Completions or Responses API call.

## 4. Execute a tool call

When the model responds with a tool call, dispatch it with
`execute_tool`:

```python
from drf_llm_gateway import execute_tool

result = execute_tool(
    "article_create",
    {"title": "Hello World", "author": 1},
    user=request.user,
)
print(result.status_code, result.data)
```

This runs through the *real* `ArticleViewSet` — the same authentication,
permission checks, and serializer validation a genuine HTTP `POST` would
go through — so there is no separate, unvalidated code path for
LLM-initiated calls.

## Next steps

- [Quick Start](quickstart.md) — the full range of field types supported,
  custom actions, examples in the schema.
- [Advanced Usage](advanced-usage.md) — MCP export, OpenAPI-adjacent
  concerns, permission modeling for agent identities.
- [Security](security.md) — read this before exposing tools to an agent
  that isn't fully trusted.
