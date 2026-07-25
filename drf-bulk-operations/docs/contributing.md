# Contributing to drf-bulk-operations

Thank you for considering a contribution. This document explains how to set
up your environment, the standards your change must meet, and how the
review process works.

## Code of Conduct

This project follows the [Code of Conduct](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-bulk-operations/CODE_OF_CONDUCT.md). By
participating, you agree to uphold it.

## Development Setup

```bash
git clone https://github.com/MahmoudGShake/MahmoudPackages.git
cd MahmoudPackages/drf-bulk-operations
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
   especially important for anything touching the atomic/non-atomic
   save logic or the URL routing in `mixins.py`, since a mistake there
   can silently change whether a partially-failed batch leaves
   committed rows behind, or reintroduce the URL-collision bug
   described in `docs/architecture.md`.
2. Fork the repository and create a branch from `main`:
   `git checkout -b feat/short-description`.
3. Write tests for your change against real models/views in
   `tests/test_app`, exercised through a real HTTP request via
   `rest_framework.test.APIClient` - not by mocking the serializer or
   the database. If your change touches routing, add or update a case
   in `tests/test_viewsets.py`'s `TestRoutingHasNoCollisions`.
4. Update documentation in `docs/` and `CHANGELOG.md` under `[Unreleased]`.
5. Ensure all quality gates above pass locally.
6. Open a pull request describing **why** the change is needed, not just
   what it does.

## Adding a new bulk mixin

Match the existing mixins' shape: one `@action(detail=False, ...)`
method with its **own, textually distinct `url_path`** - never reuse
a `url_path` already used by another bulk mixin, or the new action will
silently shadow (or be shadowed by) the existing one; see
`docs/architecture.md` for exactly why. Add a `perform_*` hook mirroring
DRF's own naming, and both an atomic and non-atomic code path returning
through `drf_bulk_operations.results.build_bulk_response` for the
non-atomic case.

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
`docs/api-reference.md` and, where relevant, illustrated with a real,
verified example in `docs/examples.md` - run
`examples/blog/example.py` (or your own scratch script) and paste the
actual output; do not hand-write example output without running it.

## Release Process

Releases are cut by the maintainer via the `release.yml` GitHub Actions
workflow, triggered by pushing a `vX.Y.Z` tag. The workflow builds the
sdist and wheel and publishes to PyPI using trusted publishing (no
long-lived tokens are stored in the repository).

## Getting Help

Open a [GitHub Discussion](https://github.com/MahmoudGShake/MahmoudPackages/discussions)
or an issue tagged `question`.
