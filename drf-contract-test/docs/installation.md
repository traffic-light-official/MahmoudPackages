# Installation

## Requirements

- Python 3.10, 3.11, 3.12, or 3.13
- Django 4.2, 5.0, 5.1, or 5.2
- Django REST Framework 3.14+
- drf-spectacular 0.27+ (used to generate live schemas)

## Install from PyPI

```bash
pip install drf-contract-test
```

There are no optional extras — `django`, `djangorestframework`,
`drf-spectacular`, `pyyaml`, `jsonschema`, and `jinja2` are all hard
dependencies, since every one of them is load-bearing for the package's
core behavior (schema generation, YAML/JSON I/O, response validation,
and HTML report rendering, respectively).

## Verify the install

```bash
drf-contract-test --help
```

You should see the `snapshot`, `compare`, and `check` subcommands listed.

To confirm the pytest plugin registered:

```bash
pytest --help | grep contract
```

You should see the `--contract-baseline`, `--contract-settings`,
`--contract-urlconf`, and `--contract-require-major-bump` options.

## Development install

```bash
git clone https://github.com/mahmoudgshaker/drf-contract-test.git
cd drf-contract-test
pip install -e ".[dev]"
```

The `dev` extra pulls in `test` (pytest, pytest-django, coverage,
hypothesis) and `docs` (mkdocs, mkdocs-material, mkdocstrings), plus
ruff, black, mypy, and the django/drf type stubs. See
[Contributing](contributing.md) for the full workflow.
