# drf-contract-test

[![CI](https://github.com/mahmoudgshake/MahmoudPackages/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/mahmoudgshaker/drf-contract-test/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/drf-contract-test.svg)](https://pypi.org/project/drf-contract-test/)
[![Python versions](https://img.shields.io/pypi/pyversions/drf-contract-test.svg)](https://pypi.org/project/drf-contract-test/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Catch breaking API changes before they ship. `drf-contract-test` compares
two OpenAPI schema snapshots (your last release vs. your current working
tree) and tells you exactly what changed — with the *correct* notion of
"breaking" for each direction: a newly-required request field is
breaking, but a newly-required response field is not; a removed response
field is breaking, but a removed (optional) request field is not.

```bash
drf-contract-test check openapi-baseline.yaml --settings myproject.settings
```

```
BREAKING GET /articles/{id}/ - responses.200.properties.internal_notes: response field removed
SAFE     GET /articles/{id}/ - responses.200.properties.view_count: new response field
BREAKING POST /articles/ - request.properties.category: is now required (was optional)

2 breaking change(s), 1 safe change(s).
2 breaking change(s) detected but the API version was not bumped (still '1.4.0').
```

The process exits non-zero whenever breaking changes are detected without a
matching version bump (pass `--no-fail-on-breaking` to only report).

## Why

Comparing raw JSON diffs of an OpenAPI schema tells you *that* something
changed, not whether it's safe. This package encodes the actual semantics
of API compatibility — informed by which side of the contract (request or
response) changed and in which direction — so you get a real signal:
"will this break an existing client," not just "something is different."

## Features

- **Directionally-correct breaking-change detection**: widening a request
  contract (new optional field, relaxed requirement) is safe; narrowing
  one (new required field, removed enum value) is breaking — and the
  reverse for responses.
- **Contract test generation**: build pytest test cases directly from an
  OpenAPI schema, validating live responses against their documented
  shape.
- **Version-bump enforcement**: fail CI if breaking changes are detected
  without a corresponding API version bump.
- **CLI** (`drf-contract-test`) with `snapshot`, `compare`, and `check`
  subcommands.
- **Pytest plugin** with fixtures and a schema-validation assertion
  helper.
- **HTML and JSON reports**, suitable for CI artifacts or PR comments.
- **CI-ready** — a single CLI command returns the right exit code to gate
  a workflow; see [Quick Start](https://mahmoudgshaker.github.io/drf-contract-test/quickstart/)
  for a drop-in GitHub Actions step.
- Fully typed, PEP 561 compatible, `mypy --strict` clean.

## Installation

```bash
pip install drf-contract-test
```

## Quick Start

```bash
# 1. Snapshot your current API as the baseline (commit this file):
drf-contract-test snapshot openapi-baseline.yaml --settings myproject.settings

# 2. Later, in CI, check for breaking changes against that baseline
#    (fails the build automatically if breaking changes lack a version bump):
drf-contract-test check openapi-baseline.yaml --settings myproject.settings --require-major-bump
```

## Documentation

Full documentation: <https://mahmoudgshaker.github.io/drf-contract-test/>

- [Getting Started](docs/getting-started.md)
- [Installation](docs/installation.md)
- [Configuration](docs/configuration.md) / [Settings](docs/settings.md)
- [Quick Start](docs/quickstart.md)
- [Advanced Usage](docs/advanced-usage.md)
- [Architecture](docs/architecture.md)
- [API Reference](docs/api-reference.md)
- [Examples](docs/examples.md)
- [Common Patterns](docs/common-patterns.md)
- [Performance](docs/performance.md)
- [Security](docs/security.md)
- [Testing](docs/testing.md)
- [Deployment](docs/deployment.md)
- [FAQ](docs/faq.md)
- [Troubleshooting](docs/troubleshooting.md)

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
