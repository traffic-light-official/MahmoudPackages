# Advanced Usage

## Multiple registries

The module-level `default_registry` is enough for most projects, but a
custom `ToolRegistry` isolates tool sets — useful for exposing different
tool sets to different agent identities, or for test isolation:

```python
from drf_llm_gateway import ToolRegistry, expose_as_tool, to_openai_tools

internal_registry = ToolRegistry()


@expose_as_tool(actions=["list", "retrieve", "create", "update", "destroy"], registry=internal_registry)
class ArticleViewSet(viewsets.ModelViewSet):
    ...


public_registry = ToolRegistry()


@expose_as_tool(actions=["list", "retrieve"], registry=public_registry, name_prefix="public_article")
class PublicArticleViewSet(viewsets.ReadOnlyModelViewSet):
    ...


internal_tools = to_openai_tools(internal_registry)
public_tools = to_openai_tools(public_registry)
```

## Custom lookup fields

If your viewset uses a non-default `lookup_field` (e.g. a slug instead of
a primary key), it's picked up automatically:

```python
class ArticleViewSet(viewsets.ModelViewSet):
    lookup_field = "slug"
    ...


@expose_as_tool(actions=["retrieve"])
class ArticleViewSet(viewsets.ModelViewSet):
    ...
```

```python
>>> registry.get("article_retrieve").input_json_schema()
{'type': 'object', 'properties': {'slug': {'type': 'string'}}, 'required': ['slug']}
```

The lookup field's JSON Schema type is inferred from the underlying model
field — a `CharField`-backed slug becomes `{"type": "string"}`, a
`UUIDField` becomes `{"type": "string", "format": "uuid"}`, and an
`AutoField`/`BigAutoField` primary key becomes `{"type": "integer"}`.

Override explicitly with `@expose_as_tool(lookup_field="slug")` if the
viewset itself doesn't declare `lookup_field`/`lookup_url_kwarg`.

## Output schemas

`serializer_to_json_schema(..., mode="output")` describes what a
serializer *returns* rather than what it accepts — every field is
included, and read-only fields are marked `"readOnly": true`. Useful for
documenting a tool's return shape to an agent framework that wants it:

```python
from drf_llm_gateway import serializer_to_json_schema

output_schema = serializer_to_json_schema(ArticleSerializer, mode="output")
```

## Per-action serializer overrides

If a viewset's `create` and `update` actions should validate against
different serializers (a common pattern when creation requires fields
that are immutable afterward):

```python
@expose_as_tool(
    actions=["create", "update"],
    serializer_classes={"create": ArticleCreateSerializer, "update": ArticleUpdateSerializer},
)
class ArticleViewSet(viewsets.ModelViewSet):
    serializer_class = ArticleSerializer  # used for list/retrieve if also exposed
    ...
```

## Schema versioning in practice

Every `ToolDefinition` exposes `schema_hash` — a content hash of its
generated input schema. Store the hash your agent framework last saw
alongside its cached copy of a tool's schema, and regenerate/re-fetch
whenever the hash changes:

```python
tool = default_registry.get("article_create")
if tool.schema_hash != cached_hash:
    # re-sync: the serializer changed since we last looked
    ...
```

Combine with the developer-supplied `version` field (set via
`ToolDefinition(..., version="2.0.0")` if constructing definitions
directly, or track it in your own registration wrapper) for
human-readable semantic versioning alongside the automatic hash.

## Building a fully custom MCP server

`to_mcp_tools()` gives you the `tools/list` response; `execute_tool()`
gives you `tools/call` dispatch. A minimal MCP server built on this
package's primitives:

```python
def handle_tools_list(request):
    return {"tools": to_mcp_tools()}


def handle_tools_call(request, user):
    name = request["params"]["name"]
    arguments = request["params"]["arguments"]
    result = execute_tool(name, arguments, user=user)
    return {"content": [{"type": "text", "text": json.dumps(result.data)}]}
```

See [Architecture](architecture.md) for how `execute_tool` maps tool-call
semantics onto DRF's real request/response cycle.
