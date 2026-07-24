# Testing

This page covers using `drf-contract-test` *from within* your own test
suite, via its pytest plugin. For testing the `drf-contract-test`
package itself, see [Contributing](contributing.md).

## Enabling the plugin

Nothing to do — it registers automatically once the package is
installed, via the `pytest11` entry point. Confirm with:

```bash
pytest --help | grep contract
```

## Failing a test on breaking changes

```python
def test_no_breaking_api_changes(contract_diff):
    assert not contract_diff.has_breaking_changes, "\n".join(
        c.message for c in contract_diff.breaking_changes
    )
```

Run with:

```bash
pytest --contract-baseline=openapi-baseline.yaml --contract-settings=myproject.settings
```

If `--contract-baseline` isn't given, this test (and anything else
requesting `contract_baseline`, `contract_diff`, or
`contract_version_check`) is **skipped**, not failed — the plugin
assumes you may not always have a baseline available (e.g. local
development without one checked out yet).

## Enforcing a version bump

```python
def test_version_bumped_for_breaking_changes(contract_version_check):
    assert contract_version_check.ok, contract_version_check.message
```

```bash
pytest --contract-baseline=openapi-baseline.yaml --contract-settings=myproject.settings \
  --contract-require-major-bump
```

## Validating live responses against the contract

`contract_cases` needs no baseline — it's built purely from the live
schema. Fixtures can't be used inside `@pytest.mark.parametrize` itself
(it runs at collection time, before fixtures are available), so
parametrize from a module-level call to `generate_contract_cases()`
instead:

```python
import pytest
from rest_framework.test import APIClient
from drf_contract_test import generate_contract_cases, generate_schema, validate_response_against_schema

_schema = generate_schema()  # DJANGO_SETTINGS_MODULE must already be set
_cases = generate_contract_cases(_schema, statuses={"200", "201"})


@pytest.mark.django_db
@pytest.mark.parametrize("case", _cases, ids=lambda c: c.operation)
def test_response_matches_contract(case):
    client = APIClient()
    response = getattr(client, case.method.lower())(case.path)
    violations = validate_response_against_schema(
        case, status_code=response.status_code, data=response.json(), root=_schema.raw
    )
    assert not violations, violations
```

See the full, runnable version in
[Examples](examples.md#generating-and-validating-contract-tests).

## Testing without a real Django project

Override the `contract_schema` fixture in your own `conftest.py` with a
hand-built `Schema` to unit-test your own contract-checking logic
without needing a full Django app:

```python
import pytest
from drf_contract_test import Schema

@pytest.fixture(scope="session")
def contract_schema():
    return Schema({"info": {"version": "1.0.0"}, "paths": {...}})
```

This is exactly the pattern this package's own test suite uses to test
the plugin itself (see `tests/test_pytest_plugin.py` in the repository).

## Running this package's own test suite

```bash
git clone https://github.com/mahmoudgshaker/drf-contract-test.git
cd drf-contract-test
pip install -e ".[dev]"
pytest --cov
```

Tests span the rules engine, schema loading/generation, contract
generation, CLI, and pytest plugin, comfortably above the 90% coverage
floor enforced by `pytest-cov`'s `fail_under` in `pyproject.toml`.
