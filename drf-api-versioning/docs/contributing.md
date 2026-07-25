# Contributing to drf-api-versioning

Thank you for considering a contribution. This document explains how to set
up your environment, the standards your change must meet, and how the
review process works.

## Code of Conduct

This project follows the [Code of Conduct](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-api-versioning/CODE_OF_CONDUCT.md). By
participating, you agree to uphold it.

## Development Setup

```bash
git clone https://github.com/MahmoudGShake/MahmoudPackages.git
cd MahmoudPackages/drf-api-versioning
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
   especially important for anything touching
   `versioning._RegistryVersioningMixin`, since it's mixed into all
   five schemes and a subtle change (e.g. to which status code an
   unknown version gets) affects every downstream project's client
   contract.
2. Fork the repository and create a branch from `main`:
   `git checkout -b feat/short-description`.
3. Write tests for your change - exercise it through a real HTTP
   request via `tests/test_app`'s views (see `docs/testing.md`), not by
   constructing a `Request`/`resolver_match` by hand, since the whole
   point of these classes is their interaction with real DRF dispatch
   machinery.
4. Update documentation in `docs/` and `CHANGELOG.md` under `[Unreleased]`.
5. Ensure all quality gates above pass locally.
6. Open a pull request describing **why** the change is needed, not just
   what it does.

## Adding a sixth versioning scheme

If DRF ever ships a new built-in scheme, add a matching class the same
way as the existing five: subclass `_RegistryVersioningMixin` and the
new DRF scheme, override `_raw_version` to extract the raw rejected
value for that scheme's resolution mechanism, and add corresponding
tests in `tests/test_versioning.py` covering known/unknown/sunset/
default-version cases through a real request, matching the existing
five classes' test coverage.

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat: add support for X`
- `fix: correct Y under Z condition`
- `docs: clarify W`
- `test: add coverage for V`
- `chore: update U`

## Public API Changes

This package follows [Semantic Versioning](https://semver.org/). Any change
to a public class, function, or setting documented in
`docs/api-reference.md` or `docs/settings.md` is a breaking change unless
purely additive, and requires a major version bump and a migration note
in `CHANGELOG.md`.

## Documentation

Documentation lives in `docs/` and is built with MkDocs:

```bash
pip install -e ".[docs]"
mkdocs serve
```

Every new public class, method, or setting must be documented in
`docs/api-reference.md`/`docs/settings.md` and, where relevant,
illustrated with a real, verified example in `docs/examples.md` - run
`examples/blog/example.py` (or your own scratch script) and paste the
actual output; do not hand-write example output without running it.
When an example uses relative dates, verify it against today's actual
date too - a date that's "safely in the future" when written can become
stale.

## Release Process

Releases are cut by the maintainer via the `release.yml` GitHub Actions
workflow, triggered by pushing a `vX.Y.Z` tag. The workflow builds the
sdist and wheel and publishes to PyPI using trusted publishing (no
long-lived tokens are stored in the repository).

## Getting Help

Open a [GitHub Discussion](https://github.com/MahmoudGShake/MahmoudPackages/discussions)
or an issue tagged `question`.
