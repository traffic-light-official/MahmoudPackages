# Contributing to drf-async

Thank you for considering a contribution. This document explains how to set
up your environment, the standards your change must meet, and how the
review process works.

## Code of Conduct

This project follows the [Code of Conduct](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-async/CODE_OF_CONDUCT.md). By
participating, you agree to uphold it.

## Development Setup

```bash
git clone https://github.com/MahmoudGShake/MahmoudPackages.git
cd MahmoudPackages/drf-async
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
   especially important for anything touching `viewsets.py`'s
   `as_view()` override or `views.py`'s `dispatch()`, since a subtle
   mistake there (e.g. forgetting `markcoroutinefunction`, or awaiting
   something in the wrong order relative to permission/throttle checks)
   changes request-handling semantics for every consumer.
2. Fork the repository and create a branch from `main`:
   `git checkout -b feat/short-description`.
3. Write tests for your change as `async def` test functions exercising
   real dispatch (via `AsyncClient`/`AsyncRequestFactory` against a real
   view, not by calling internal methods directly where avoidable) -
   and use `@pytest.mark.django_db(transaction=True)`, not the default,
   for any test touching the database; see
   [Testing](testing.md#the-one-thing-you-must-get-right-use-transactiontrue-for-async-database-tests)
   for why the default silently leaks data between async tests.
4. Update documentation in `docs/` and `CHANGELOG.md` under `[Unreleased]`.
5. Ensure all quality gates above pass locally.
6. Open a pull request describing **why** the change is needed, not just
   what it does.

## Adding a new async mixin or concrete generic view

Match DRF's own naming and shape exactly: the action method name must
match what a standard router (for a viewset mixin) or DRF's own
concrete generics module (for a standalone view) uses - see
[Architecture](architecture.md#why-the-crud-action-methods-are-named-listcreate-and-not-alistacreate)
for why this isn't just a style preference. Internal helper methods you
introduce yourself (not looked up by name from outside) should keep the
`a`-prefix convention (`aperform_x`, matching Django's own async ORM
naming), the same way `aperform_create`/`aperform_update`/
`aperform_destroy` do.

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
