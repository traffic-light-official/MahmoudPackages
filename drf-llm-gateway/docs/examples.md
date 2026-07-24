# Examples

Runnable versions live in
[`examples/`](https://github.com/mahmoudgshaker/drf-llm-gateway/tree/main/examples).

## A complete blog agent backend

```python
# models.py
from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()


class Article(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    title = models.CharField(max_length=255)
    body = models.TextField(blank=True, default="")
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="articles")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
```

```python
# serializers.py
from rest_framework import serializers


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ["id", "title", "body", "author", "status"]
        read_only_fields = ["id"]
```

```python
# views.py
from rest_framework import viewsets
from drf_llm_gateway import expose_as_tool


@expose_as_tool(
    actions=["list", "retrieve", "create", "partial_update"],
    examples={"create": [{"title": "My First Post", "body": "Hello!", "author": 1}]},
)
class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
```

## Wiring into an OpenAI Chat Completions loop

```python
import openai
from drf_llm_gateway import execute_tool, to_openai_tools

client = openai.OpenAI()
tools = to_openai_tools()

response = client.chat.completions.create(
    model="gpt-4.1",
    messages=[{"role": "user", "content": "Create a draft article titled 'Hello'"}],
    tools=tools,
)

for tool_call in response.choices[0].message.tool_calls or []:
    import json

    arguments = json.loads(tool_call.function.arguments)
    result = execute_tool(tool_call.function.name, arguments, user=request.user)
    print(result.status_code, result.data)
```

## Wiring into an MCP server

```python
from drf_llm_gateway import execute_tool, to_mcp_tools


def list_tools() -> dict:
    return {"tools": to_mcp_tools()}


def call_tool(name: str, arguments: dict, *, user) -> dict:
    result = execute_tool(name, arguments, user=user)
    return {"content": [{"type": "text", "text": str(result.data)}], "isError": result.status_code >= 400}
```

## A read-only public tool set alongside a full internal one

```python
@expose_as_tool(actions=["list", "retrieve", "create", "update", "partial_update", "destroy"])
class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]


@expose_as_tool(actions=["list", "retrieve"], name_prefix="public_article")
class PublicArticleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Article.objects.filter(status=Article.Status.PUBLISHED)
    serializer_class = ArticleSerializer
    permission_classes = []
```

An anonymous agent identity (`execute_tool(..., user=None)`) can call
`public_article_list`/`public_article_retrieve` but is denied (raises
`ToolPermissionDeniedError`) on the internal `article_*` tools.
