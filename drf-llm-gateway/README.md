# drf-llm-gateway

[![PyPI version](https://img.shields.io/pypi/v/drf-llm-gateway.svg)](https://pypi.org/project/drf-llm-gateway/)
[![Python versions](https://img.shields.io/pypi/pyversions/drf-llm-gateway.svg)](https://pypi.org/project/drf-llm-gateway/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Turn your existing Django REST Framework viewsets into tools an LLM can
call — OpenAI function-calling format, MCP (Model Context Protocol) tool
format, or plain JSON Schema — generated automatically from the
serializers you already have.

```python
from rest_framework import viewsets
from drf_llm_gateway import expose_as_tool


@expose_as_tool(actions=["list", "retrieve", "create"])
class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
```

```python
from drf_llm_gateway import default_registry
from drf_llm_gateway.openai_tools import to_openai_tools

tools = to_openai_tools(default_registry)
# [{"type": "function", "function": {"name": "article_list", "description": "...",
#   "parameters": {"type": "object", "properties": {...}}}}, ...]
```

## Why

Wiring an LLM agent up to call your existing API usually means hand-writing
and hand-maintaining a parallel set of tool/function schemas — which drift
out of sync with your serializers the moment either side changes. This
package derives the schema *from the serializer itself* at generation
time, so there is nothing to keep in sync: change a field on the
serializer, regenerate the tools, done.

## Features

- **Automatic JSON Schema generation** from any DRF serializer — every
  standard field type, nested serializers, list serializers, related
  fields, choice fields, and more.
- **OpenAI function-calling format** and **MCP tool format** exporters.
- **Tool registry** — a decorator (`@expose_as_tool`) that registers a
  viewset's actions as callable tools without any schema duplication.
- **Runtime executor** — validates arguments against the real serializer
  and dispatches to the real viewset action, respecting DRF permission and
  authentication classes.
- **Auth/permission metadata** attached to every tool definition, so a
  gateway can decide what an agent identity may call before it calls it.
- **Schema versioning** — every generated tool carries a content hash that
  changes whenever its schema changes, so consumers can detect drift.
- **CLI** (`generate_llm_tools` management command) to export the full
  tool set as JSON for any external agent framework.
- Fully typed, PEP 561 compatible, `mypy --strict` clean.

## Installation

```bash
pip install drf-llm-gateway
```

Requires Python 3.10+, Django 4.2+, and Django REST Framework 3.14+.

## Quick Start

See [`docs/quickstart.md`](docs/quickstart.md) for a complete walkthrough,
including calling a tool end-to-end from a validated argument dict.

## Documentation

Full documentation: <https://mahmoudgshake.github.io/MahmoudPackages/drf-llm-gateway>

- [Getting Started](https://mahmoudgshake.github.io/MahmoudPackages/drf-llm-gateway/getting-started)
- [Installation](https://mahmoudgshake.github.io/MahmoudPackages/drf-llm-gateway/installation)
- [Configuration](https://mahmoudgshake.github.io/MahmoudPackages/drf-llm-gateway/configuration) / [Settings](https://mahmoudgshake.github.io/MahmoudPackages/drf-llm-gateway/settings)
- [Quick Start](https://mahmoudgshake.github.io/MahmoudPackages/drf-llm-gateway/quickstart)
- [Advanced Usage](https://mahmoudgshake.github.io/MahmoudPackages/drf-llm-gateway/advanced-usage)
- [Architecture](https://mahmoudgshake.github.io/MahmoudPackages/drf-llm-gateway/architecture)
- [API Reference](https://mahmoudgshake.github.io/MahmoudPackages/drf-llm-gateway/api-reference)
- [Examples](https://mahmoudgshake.github.io/MahmoudPackages/drf-llm-gateway/examples)
- [Common Patterns](https://mahmoudgshake.github.io/MahmoudPackages/drf-llm-gateway/common-patterns)
- [Performance](https://mahmoudgshake.github.io/MahmoudPackages/drf-llm-gateway/performance)
- [Security](https://mahmoudgshake.github.io/MahmoudPackages/drf-llm-gateway/security)
- [Testing](https://mahmoudgshake.github.io/MahmoudPackages/drf-llm-gateway/testing)
- [Deployment](https://mahmoudgshake.github.io/MahmoudPackages/drf-llm-gateway/deployment)
- [FAQ](https://mahmoudgshake.github.io/MahmoudPackages/drf-llm-gateway/faq)
- [Troubleshooting](https://mahmoudgshake.github.io/MahmoudPackages/drf-llm-gateway/troubleshooting)

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-llm-gateway/CONTRIBUTING.md).

## License

MIT — see [LICENSE](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-llm-gateway/LICENSE).
