# Installation

## Requirements

| Dependency | Supported versions |
| --- | --- |
| Python | 3.10, 3.11, 3.12, 3.13 |
| Django | 4.2, 5.0, 5.1, 5.2 |
| Django REST Framework | 3.14+ |

## Standard install

```bash
pip install drf-llm-gateway
```

There are no optional extras — the package's only runtime dependencies are
Django and DRF.

## Django project setup

`INSTALLED_APPS` entry is **optional**:

```python
INSTALLED_APPS = [
    ...,
    "drf_llm_gateway",
]
```

Only add it if you plan to use the `generate_llm_tools` management
command — Django only discovers management commands from apps listed in
`INSTALLED_APPS`. `expose_as_tool`, `execute_tool`,
`serializer_to_json_schema`, `to_openai_tools`, and `to_mcp_tools` all work
without this entry.

## Verifying the install

```bash
python -c "import drf_llm_gateway; print(drf_llm_gateway.__version__)"
```

## Upgrading

Check [CHANGELOG.md](https://github.com/mahmoudgshaker/drf-llm-gateway/blob/main/CHANGELOG.md)
before upgrading across a major version — this package follows
[Semantic Versioning](https://semver.org/).
