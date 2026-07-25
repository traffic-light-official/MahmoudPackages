# Contributing to drf-changelog-generator

Thank you for considering a contribution. This document explains how to set
up your environment, the standards your change must meet, and how the
review process works.

## Code of Conduct

This project follows the [Code of Conduct](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-changelog-generator/CODE_OF_CONDUCT.md). By
participating, you agree to uphold it.

## Development Setup

```bash
git clone https://github.com/MahmoudGShake/MahmoudPackages.git
cd MahmoudPackages/drf-changelog-generator
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

1. Open an issue first for anything beyond a trivial fix, so the approach
   can be discussed before you invest time - this is especially important
   for anything touching the breaking-vs-non-breaking classification in
   `diffing/engine.py`, since that rule set is the whole point of this
   package and changing it silently changes what every downstream CI
   gate considers "safe."
2. Fork the repository and create a branch from `main`:
   `git checkout -b feat/short-description`.
3. Write tests for your change. Untested code will not be merged.
4. Update documentation in `docs/` and `CHANGELOG.md` under `[Unreleased]`.
5. Ensure all quality gates above pass locally.
6. Open a pull request describing **why** the change is needed, not just
   what it does.

## Changing the breaking-change rule set

Any change to a classification in
[the rule table](architecture.md#the-breaking-change-rule-set) is a
breaking change to this package itself (a project that was relying on a
given change being non-breaking could suddenly start failing
`--fail-on-breaking` after an upgrade), and requires:

- An update to the table in `docs/architecture.md`.
- A new or updated test in `tests/test_diffing_engine.py` covering the
  exact scenario.
- A major version bump and a clear migration note in `CHANGELOG.md`
  explaining exactly which change kind's severity changed and why.

## Adding a new output format

A renderer is a plain function taking a `SchemaDiff` and keyword-only
`old_ref`/`new_ref` (see `rendering/markdown.py` for the simplest
example) - build it on top of `rendering.common.summarize()` rather than
re-partitioning `SchemaDiff.changes` yourself, so every format stays in
sync on what counts as "breaking" vs. "added" vs. "deprecated." Wire it
into `cli.py`'s `_FORMATS` tuple and `_render()`, and the management
command's `--format` choices if applicable.

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat: add support for X`
- `fix: correct Y under Z condition`
- `docs: clarify W`
- `test: add coverage for V`
- `chore: update U`

## Public API Changes

This package follows [Semantic Versioning](https://semver.org/). Any change
to a public class, function, or CLI flag documented in
`docs/api-reference.md` or `docs/settings.md` is a breaking change unless
purely additive, and requires a major version bump and a migration note
in `CHANGELOG.md`.

## Documentation

Documentation lives in `docs/` and is built with MkDocs:

```bash
pip install -e ".[docs]"
mkdocs serve
```

Every new public class, method, or CLI flag must be documented in
`docs/api-reference.md`/`docs/settings.md` and, where relevant,
illustrated with a real, verified example in `docs/examples.md` - run
the CLI against `examples/blog/`'s schemas (or your own scratch schemas)
and paste the actual output; do not hand-write example output without
running it, since the exact wording and ordering are easy to get subtly
wrong.

## Release Process

Releases are cut by the maintainer via the `release.yml` GitHub Actions
workflow, triggered by pushing a `vX.Y.Z` tag. The workflow builds the
sdist and wheel and publishes to PyPI using trusted publishing (no
long-lived tokens are stored in the repository).

## Getting Help

Open a [GitHub Discussion](https://github.com/MahmoudGShake/MahmoudPackages/discussions)
or an issue tagged `question`.
