# Contributing to drf-async

Thank you for considering a contribution. This document explains how to set
up your environment, the standards your change must meet, and how the
review process works.

## Code of Conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md). By
participating, you agree to uphold it.

## Development Setup

```bash
git clone https://github.com/mahmoudgshaker/drf-async.git
cd drf-async
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install
```

## Running the Test Suite

```bash
pytest
```

Run the full compatibility matrix (all supported Python and Django
versions) with [tox](https://tox.wiki):

```bash
tox
```

Run a single environment:

```bash
tox -e py312-django50
```

## Code Quality Gates

Every pull request must pass:

- **ruff** - linting (`ruff check .`)
- **black** - formatting (`black --check .`)
- **mypy --strict** - static typing (`mypy src`)
- **pytest** - full test suite with coverage
- **pre-commit** - all configured hooks (`pre-commit run --all-files`)

These all run automatically in CI, but running them locally first saves
review round-trips.

## Making a Change

1. Open an issue first for anything beyond a trivial fix, so the
   approach can be discussed before you invest time - this is
   especially important for anything touching sync/async bridging
   (`compat.py`, `AsyncAPIView.ainitial`), since a mistake there can
   manifest as a `SynchronousOnlyOperation` error only under real
   concurrent load, not in a quick manual check.
2. Fork the repository and create a branch from `main`:
   `git checkout -b feat/short-description`.
3. Write tests for your change against real models/views in
   `tests/test_app`, exercised through `django.test.AsyncClient` - not
   by mocking the async ORM or `sync_to_async`.
4. Update documentation in `docs/` and `CHANGELOG.md` under `[Unreleased]`.
5. Ensure all quality gates above pass locally.
6. Open a pull request describing **why** the change is needed, not just
   what it does.

## Adding support for a new DRF built-in class

If DRF ships a new mixin/generic view/viewset base, add a matching
async equivalent the same way as the existing ones: same action method
names as the sync version (required for router compatibility - see
`docs/architecture.md`), bridging any database-touching sync call via
`sync_to_async(..., thread_sensitive=True)`, and a real end-to-end test
through `AsyncClient` proving no `SynchronousOnlyOperation` is raised.

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat: add support for X`
- `fix: correct Y under Z condition`
- `docs: clarify W`
- `test: add coverage for V`
- `chore: update U`

## Public API Changes

This package follows [Semantic Versioning](https://semver.org/). Any change
to a public class or function documented in `docs/api-reference.md` is
a breaking change unless purely additive, and requires a major version
bump and a migration note in `CHANGELOG.md`.

## Documentation

Documentation lives in `docs/` and is built with MkDocs:

```bash
pip install -e ".[docs]"
mkdocs serve
```

Every new public class or method must be documented in
`docs/api-reference.md` and, where relevant, illustrated in
`docs/examples.md`.

## Release Process

Releases are cut by the maintainer via the `release.yml` GitHub Actions
workflow, triggered by pushing a `vX.Y.Z` tag. The workflow builds the
sdist and wheel and publishes to PyPI using trusted publishing (no
long-lived tokens are stored in the repository).

## Getting Help

Open a [GitHub Discussion](https://github.com/mahmoudgshaker/drf-async/discussions)
or an issue tagged `question`.
