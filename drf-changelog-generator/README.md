# drf-changelog-generator

[![PyPI version](https://img.shields.io/pypi/v/drf-changelog-generator.svg)](https://pypi.org/project/drf-changelog-generator/)
[![Python versions](https://img.shields.io/pypi/pyversions/drf-changelog-generator.svg)](https://pypi.org/project/drf-changelog-generator/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Generate a changelog by diffing two OpenAPI schema versions - detecting
breaking changes, added/removed/deprecated endpoints, and field-level
request/response changes - and render it as Markdown, HTML, Slack
Block Kit, or GitHub Release notes. Ships as both a library and a
standalone CLI.

```bash
drf-changelog-generator diff \
  --repo . --old-ref v1.0.0 --new-ref v1.1.0 \
  --schema-path api/schema.yml --format markdown
```

```markdown
# API Changelog: `v1.0.0` -> `v1.1.0`

## Breaking Changes

- `DELETE /articles/{id}/`: Removed field 'legacy_id'

## Added Endpoints

- `GET /articles/{id}/comments/`: Added GET /articles/{id}/comments/

## Non-Breaking Changes

- `POST /articles/`: Added field 'tags'
```

## Why

Reviewing a raw OpenAPI schema diff by eye to answer "did we just break
someone's integration" does not scale past a handful of endpoints, and
most teams don't do it consistently. This package turns that diff into
an explicit, opinionated breaking/non-breaking classification (documented
in full - see [`docs/architecture.md`](docs/architecture.md)) and a
changelog format ready to drop into a PR description, a Slack channel,
or a GitHub Release - as a CI gate, not just documentation.

## Features

- **Structural OpenAPI diffing**: paths, operations, parameters,
  request bodies, and response schemas, including nested object and
  array fields (with `$ref` resolution).
- **Explicit breaking-change classification** - one documented rule
  set, not a black box.
- **Four output formats**: Markdown, self-contained HTML, Slack Block
  Kit (with an optional webhook post), and GitHub Release notes.
- **A standalone CLI** (`drf-changelog-generator`) that needs no Django
  project at all if you already have two schema files.
- **Git-native**: diff schemas as they existed at two tags/branches/commits
  via `git show`, no checkout required.
- **CI-ready**: `--fail-on-breaking` exits non-zero when breaking
  changes are detected, and a ready-to-use [GitHub Action](action.yml)
  wraps the CLI.
- **Optional Django management command** (`generate_changelog`) for
  projects using `drf-spectacular`, diffing the *current* working-tree
  schema against a previous Git ref.
- **Fully typed**, PEP 561 compatible, `mypy --strict` clean.

## Installation

```bash
pip install drf-changelog-generator
```

Requires Python 3.10+. Django and Django REST Framework are declared
dependencies (for the optional management command and to match the
rest of this project's support matrix), but the CLI and library work
standalone with just two schema files - no Django project required.

## Quick Start

Comparing two committed schema files directly:

```bash
drf-changelog-generator diff --old-file old-schema.yml --new-file new-schema.yml
```

Comparing two Git tags, reading the schema file from history at each:

```bash
drf-changelog-generator diff \
  --repo /path/to/project --old-ref v1.0.0 --new-ref v1.1.0 \
  --schema-path api/schema.yml --format github --repo-slug myorg/myproject \
  --fail-on-breaking
```

From Python:

```python
from drf_changelog_generator import diff_schemas, load_schema_file, render_markdown

old = load_schema_file("old-schema.yml")
new = load_schema_file("new-schema.yml")
diff = diff_schemas(old, new)
print(render_markdown(diff, old_ref="v1.0.0", new_ref="v1.1.0"))
```

See [`docs/quickstart.md`](docs/quickstart.md) for the Django management
command and the GitHub Action.

## Documentation

Full documentation is available at
[Documentation Home Page](https://mahmoudgshake.github.io/MahmoudPackages/drf-changelog-generator/), including:

- [Getting Started](https://mahmoudgshake.github.io/MahmoudPackages/drf-changelog-generator/getting-started)
- [Installation](https://mahmoudgshake.github.io/MahmoudPackages/drf-changelog-generator/installation)
- [Configuration](https://mahmoudgshake.github.io/MahmoudPackages/drf-changelog-generator/configuration) / [Settings](https://mahmoudgshake.github.io/MahmoudPackages/drf-changelog-generator/settings)
- [Quick Start](https://mahmoudgshake.github.io/MahmoudPackages/drf-changelog-generator/quickstart)
- [Advanced Usage](https://mahmoudgshake.github.io/MahmoudPackages/drf-changelog-generator/advanced-usage)
- [Architecture](https://mahmoudgshake.github.io/MahmoudPackages/drf-changelog-generator/architecture)
- [API Reference](https://mahmoudgshake.github.io/MahmoudPackages/drf-changelog-generator/api-reference)
- [Examples](https://mahmoudgshake.github.io/MahmoudPackages/drf-changelog-generator/examples)
- [Common Patterns](https://mahmoudgshake.github.io/MahmoudPackages/drf-changelog-generator/common-patterns)
- [Performance](https://mahmoudgshake.github.io/MahmoudPackages/drf-changelog-generator/performance)
- [Security](https://mahmoudgshake.github.io/MahmoudPackages/drf-changelog-generator/security)
- [Testing](https://mahmoudgshake.github.io/MahmoudPackages/drf-changelog-generator/testing)
- [Deployment](https://mahmoudgshake.github.io/MahmoudPackages/drf-changelog-generator/deployment)
- [FAQ](https://mahmoudgshake.github.io/MahmoudPackages/drf-changelog-generator/faq)
- [Troubleshooting](https://mahmoudgshake.github.io/MahmoudPackages/drf-changelog-generator/troubleshooting)

## Contributing

Contributions are welcome — see [Contributing](https://mahmoudgshake.github.io/MahmoudPackages/drf-changelog-generator/contributing).

## License

MIT — see [LICENSE](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-changelog-generator/LICENSE).
