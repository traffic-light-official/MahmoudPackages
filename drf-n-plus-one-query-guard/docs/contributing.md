# Contributing to drf-n-plus-one-query-guard

Thank you for considering a contribution. This document explains how to set
up your environment, the standards your change must meet, and how the
review process works.

## Code of Conduct

This project follows the [Code of Conduct](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-n-plus-one-query-guard/CODE_OF_CONDUCT.md). By
participating, you agree to uphold it.

## Development Setup

```bash
git clone https://github.com/MahmoudGShake/MahmoudPackages.git
cd MahmoudPackages/drf-n-plus-one-query-guard
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
   especially important for anything touching fingerprinting
   (`fingerprint.py`) or call-site resolution
   (`tracker._first_application_frame`), since both directly affect
   what every downstream project sees as "the same query" or "the
   responsible code."
2. Fork the repository and create a branch from `main`:
   `git checkout -b feat/short-description`.
3. Write tests for your change against the real `tests/test_app`
   models/viewsets (`Article`/`Author`) rather than mocking
   `connection.execute_wrapper()` - exercising the real SQLite backend
   is what actually validates fingerprinting and call-site behavior.
4. Update documentation in `docs/` and `CHANGELOG.md` under `[Unreleased]`.
5. Ensure all quality gates above pass locally.
6. Open a pull request describing **why** the change is needed, not just
   what it does.

## Changing what counts as a "library frame" for call-site resolution

Any change to `tracker._is_library_frame`'s marker list is a behavior
change to every downstream project's reported call sites - add a test
in `tests/test_tracker.py` demonstrating the specific frame shape being
included/excluded, and document the change in `CHANGELOG.md`.

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
`docs/api-reference.md` and, where relevant, illustrated with a real,
verified example in `docs/examples.md` - run `examples/blog/example.py`
(or your own scratch script) and paste the actual output; do not
hand-write example output without running it.

## Release Process

Releases are cut by the maintainer via the `release.yml` GitHub Actions
workflow, triggered by pushing a `vX.Y.Z` tag. The workflow builds the
sdist and wheel and publishes to PyPI using trusted publishing (no
long-lived tokens are stored in the repository).

## Getting Help

Open a [GitHub Discussion](https://github.com/MahmoudGShake/MahmoudPackages/discussions)
or an issue tagged `question`.
