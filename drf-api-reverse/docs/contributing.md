# Contributing to drf-api-reverse

Thank you for considering a contribution. This document explains how to set
up your environment, the standards your change must meet, and how the
review process works.

## Code of Conduct

This project follows the [Code of Conduct](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-api-reverse/CODE_OF_CONDUCT.md). By
participating, you agree to uphold it.

## Development Setup

```bash
git clone https://github.com/MahmoudGShake/MahmoudPackages.git
cd MahmoudPackages/drf-api-reverse
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
   especially important for anything touching operation classification
   (`codegen/operations.py`) or the region-merge engine
   (`regions.py`), since both are load-bearing for every downstream
   project's generated code.
2. Fork the repository and create a branch from `main`:
   `git checkout -b feat/short-description`.
3. Write tests for your change. Untested code will not be merged.
4. Update documentation in `docs/` and `CHANGELOG.md` under `[Unreleased]`.
5. Ensure all quality gates above pass locally.
6. Open a pull request describing **why** the change is needed, not just
   what it does.

## Adding support for a new path shape

Adding a new automatically-classified path shape (beyond
collection/detail/one-level-nested) requires updating
[the classification table](architecture.md#resource-grouping-and-operation-classification)
in `docs/architecture.md`, a new case in
`codegen/operations.py::_classify`, corresponding generation logic in
`codegen/views.py`, and test coverage in `tests/test_codegen_operations.py`
and `tests/test_codegen_views.py` for the new shape.

## Adding a new JSON Schema type/format mapping

Add the mapping to `type_mapping.py`'s `_STRING_FORMAT_FIELDS` or
`_SIMPLE_TYPE_FIELDS` (or a new branch in `field_spec` for a shape
that doesn't fit either), and a test in `tests/test_type_mapping.py`
covering the exact field expression produced.

## Any change to what gets written into generated files must go through `naming`/`repr()`/`comment_safe`

If your change interpolates schema-derived text (a path, a `$ref`
target, an `operationId`) into generated source, it must go through
`naming.to_class_name`/`to_snake_case` (identifiers), `repr()` (string
literals), or `naming.comment_safe` (comments) - never a raw f-string
substitution. See [Security](security.md) for why, and add a test with
a deliberately adversarial value (an embedded quote, an embedded
newline) alongside the normal-case test.

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
`drf-api-reverse scaffold` against `examples/blog/contract.yml` (or your
own scratch schema) and paste the actual output; do not hand-write
example output without running it.

## Release Process

Releases are cut by the maintainer via the `release.yml` GitHub Actions
workflow, triggered by pushing a `vX.Y.Z` tag. The workflow builds the
sdist and wheel and publishes to PyPI using trusted publishing (no
long-lived tokens are stored in the repository).

## Getting Help

Open a [GitHub Discussion](https://github.com/MahmoudGShake/MahmoudPackages/discussions)
or an issue tagged `question`.
