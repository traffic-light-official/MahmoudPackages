# Quick Start

## Registering standard actions

```python
@expose_as_tool(actions=["list", "retrieve", "create", "update", "partial_update", "destroy"])
class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
```

Each action becomes one tool:

| Action | Tool name | HTTP method | Input schema |
| --- | --- | --- | --- |
| `list` | `article_list` | GET | `{}` |
| `retrieve` | `article_retrieve` | GET | `{pk}` |
| `create` | `article_create` | POST | writable serializer fields |
| `update` | `article_update` | PUT | `{pk}` + all writable fields (required) |
| `partial_update` | `article_partial_update` | PATCH | `{pk}` + writable fields (none required) |
| `destroy` | `article_destroy` | DELETE | `{pk}` |

## Registering a custom `@action`

```python
class ArticleViewSet(viewsets.ModelViewSet):
    ...

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        article = self.get_object()
        article.status = Article.Status.PUBLISHED
        article.save(update_fields=["status"])
        return Response(self.get_serializer(article).data)


@expose_as_tool(actions=["list", "retrieve", "publish"])
class ArticleViewSet(viewsets.ModelViewSet):
    ...
```

Custom actions are introspected via the `@action` decorator's own
`.mapping`/`.detail` attributes — no extra configuration is needed as long
as the method is decorated with `@action`.

## Every field type your serializers already use

`serializer_to_json_schema` (used internally by every tool's
`input_json_schema()`) supports:

- Standard scalars: `CharField`, `IntegerField`, `FloatField`,
  `BooleanField`, `DecimalField` (as a string, to avoid float precision
  loss), `EmailField`, `URLField`, `UUIDField`, `SlugField`,
  `DateField`/`DateTimeField`/`TimeField`/`DurationField`.
- `ChoiceField` / `MultipleChoiceField` — becomes a JSON Schema `enum`
  (capped by [`MAX_ENUM_VALUES`](settings.md#max_enum_values)).
- Nested `Serializer` and `ListSerializer` (`many=True`) — recursively
  converted, up to [`MAX_SCHEMA_DEPTH`](settings.md#max_schema_depth).
- `PrimaryKeyRelatedField`, `SlugRelatedField`, `StringRelatedField`,
  `HyperlinkedRelatedField`, and their `many=True` (`ManyRelatedField`)
  variants.
- `ListField` with any child field type.

Not supported: `FileField` / `ImageField` (an LLM cannot attach binary
file content to a tool call) — see
[Troubleshooting](troubleshooting.md#a-field-doesnt-appear-in-the-generated-schema).

## Attaching examples

```python
@expose_as_tool(
    actions=["create"],
    examples={"create": [{"title": "Hello World", "author": 1}]},
)
class ArticleViewSet(viewsets.ModelViewSet):
    ...
```

```python
>>> registry.get("article_create").input_json_schema()["examples"]
[{'title': 'Hello World', 'author': 1}]
```

## Exporting for MCP instead of OpenAI

```python
from drf_llm_gateway import to_mcp_tools

tools = to_mcp_tools()
# [{"name": "article_list", "description": "...", "inputSchema": {...}}, ...]
```

## Exporting from the command line

```bash
python manage.py generate_llm_tools --format openai > tools.json
python manage.py generate_llm_tools --format mcp --indent 0
python manage.py generate_llm_tools --format jsonschema
```

## Next steps

- [Advanced Usage](advanced-usage.md) — multiple registries, custom
  lookup fields, output schemas.
- [Security](security.md) — permission modeling for agent identities.
