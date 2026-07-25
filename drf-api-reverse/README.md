# drf-api-reverse

[![PyPI version](https://img.shields.io/pypi/v/drf-api-reverse.svg)](https://pypi.org/project/drf-api-reverse/)
[![Python versions](https://img.shields.io/pypi/pyversions/drf-api-reverse.svg)](https://pypi.org/project/drf-api-reverse/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Design-first DRF scaffolding: generate `serializers.py`, `views.py`, and
`urls.py` directly from an OpenAPI contract, so the shape of your API
is written once, in one place, and the Django REST Framework code
follows from it - not the other way around. Regeneration is idempotent
(hand-written code survives a re-run) and drift between the contract
and the generated code is detectable in CI.

```bash
drf-api-reverse scaffold --schema api/contract.yml --output myapp/
```

```
Created myapp/serializers.py
Created myapp/views.py
Created myapp/urls.py
```

## Why

Code-first DRF (models -> serializers -> views -> schema, via
`drf-spectacular`) works well once an API exists, but a design-first
team wants to agree on the contract *before* writing a single line of
Django. `drf-api-reverse` generates the DRF-side scaffolding directly
from that agreed-upon OpenAPI contract, so implementers start from a
correct, matching shape instead of hand-translating a spec document
into serializer fields by eye.

## Features

- **Serializer generation**: one `serializers.Serializer` per
  `components.schemas` entry, with DRF field types mapped from JSON
  Schema type/format/enum, nested `$ref`s resolved to nested
  serializers, and dependency-ordered class emission.
- **ViewSet generation**: one `ViewSet` per resource, with
  `list`/`create`/`retrieve`/`update`/`partial_update`/`destroy`
  methods mapped from standard collection/detail paths, and
  `@action`-decorated methods for one level of nested sub-resource
  paths (e.g. `/articles/{id}/comments/`).
- **Idempotent regeneration**: every generated file is split into
  named, marker-delimited regions - re-running `scaffold` after the
  contract changes updates only the regions whose schema changed,
  leaving your hand-written code (inside or outside of regions)
  untouched.
- **Drift detection**: `drf-api-reverse check` compares on-disk
  generated regions against what the current contract would produce,
  and exits non-zero in CI if they've fallen out of sync.
- **A standalone CLI** (`drf-api-reverse`) that needs no Django project
  at all - only a schema file and an output directory.
- **Optional Django management command** (`scaffold_api`) for projects
  that would rather trigger this via `manage.py`.
- **Fully typed**, PEP 561 compatible, `mypy --strict` clean.

## Installation

```bash
pip install drf-api-reverse
```

Requires Python 3.10+. Django and Django REST Framework are declared
dependencies (for the optional management command and to match the
rest of this project's support matrix), but the CLI and library work
standalone - no Django project required to scaffold or check.

## Quick Start

```bash
drf-api-reverse scaffold --schema api/contract.yml --output myapp/
```

Re-run any time the contract changes - existing hand-written code is
preserved:

```bash
drf-api-reverse scaffold --schema api/contract.yml --output myapp/
```

Gate CI on drift between the contract and what's committed:

```bash
drf-api-reverse check --schema api/contract.yml --output myapp/
```

From Python:

```python
from drf_api_reverse import load_schema_file, scaffold

schema = load_schema_file("api/contract.yml")
for result in scaffold(schema, "myapp/"):
    print(f"{'Created' if result.created else 'Updated'} {result.filename}")
```

See [`docs/quickstart.md`](docs/quickstart.md) for the Django management
command.

## Documentation

Full documentation is available at
[Documentation Home Page](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-reverse/), including:

- [Getting Started](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-reverse/getting-started)
- [Installation](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-reverse/installation)
- [Configuration](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-reverse/configuration) / [Settings](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-reverse/settings)
- [Quick Start](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-reverse/quickstart)
- [Advanced Usage](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-reverse/advanced-usage)
- [Architecture](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-reverse/architecture)
- [API Reference](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-reverse/api-reference)
- [Examples](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-reverse/examples)
- [Common Patterns](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-reverse/common-patterns)
- [Performance](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-reverse/performance)
- [Security](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-reverse/security)
- [Testing](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-reverse/testing)
- [Deployment](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-reverse/deployment)
- [FAQ](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-reverse/faq)
- [Troubleshooting](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-reverse/troubleshooting)

## Contributing

Contributions are welcome — see [Contributing](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-reverse/contributing).

## License

MIT — see [LICENSE](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-api-reverse/LICENSE).
