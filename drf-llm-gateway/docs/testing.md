# Testing

## Running the package's own test suite

```bash
git clone https://github.com/mahmoudgshaker/drf-llm-gateway.git
cd drf-llm-gateway
pip install -e ".[dev]"
pytest
tox  # full Python/Django compatibility matrix
```

## Testing your own tool registrations

### Asserting a tool's schema shape

```python
from drf_llm_gateway import default_registry


def test_article_create_tool_schema():
    tool = default_registry.get("article_create")
    schema = tool.input_json_schema()
    assert schema["properties"]["title"] == {"type": "string"}
    assert "title" in schema["required"]
```

### Testing execution end-to-end

```python
import pytest
from drf_llm_gateway import execute_tool
from drf_llm_gateway.exceptions import ToolPermissionDeniedError, ToolValidationError


@pytest.mark.django_db
def test_create_article_via_tool(author, user):
    result = execute_tool("article_create", {"title": "Hi", "author": author.pk}, user=user)
    assert result.status_code == 201


@pytest.mark.django_db
def test_anonymous_call_is_denied():
    with pytest.raises(ToolPermissionDeniedError):
        execute_tool("article_create", {"title": "Hi"})


@pytest.mark.django_db
def test_invalid_arguments_raise_validation_error(user):
    with pytest.raises(ToolValidationError):
        execute_tool("article_create", {}, user=user)  # missing required fields
```

### Using an isolated registry in tests

Avoid polluting the module-level `default_registry` across test modules by
building a scratch registry for tests that register throwaway viewsets:

```python
from drf_llm_gateway import ToolRegistry, expose_as_tool


def test_custom_registration():
    registry = ToolRegistry()

    @expose_as_tool(actions=["list"], registry=registry)
    class ScratchViewSet(viewsets.ReadOnlyModelViewSet):
        queryset = Article.objects.all()
        serializer_class = ArticleSerializer

    assert registry.get("scratch_list") is not None
    assert len(registry) == 1
```

## Testing OpenAI/MCP export shape

```python
from drf_llm_gateway import to_openai_tools, to_mcp_tools


def test_openai_export_shape():
    tools = to_openai_tools()
    assert all(t["type"] == "function" for t in tools)
    assert all("parameters" in t["function"] for t in tools)


def test_mcp_export_shape():
    tools = to_mcp_tools()
    assert all("inputSchema" in t for t in tools)
```

## Testing the management command

```python
from io import StringIO
import json
from django.core.management import call_command


def test_generate_llm_tools_command():
    out = StringIO()
    call_command("generate_llm_tools", format="openai", stdout=out)
    payload = json.loads(out.getvalue())
    assert isinstance(payload, list)
```

## Validating generated schemas against the JSON Schema spec

If you want an extra layer of confidence that generated schemas are valid
JSON Schema (not just "looks right"), validate with the `jsonschema`
package's own meta-schema:

```python
import jsonschema

jsonschema.Draft202012Validator.check_schema(tool.input_json_schema())
```
