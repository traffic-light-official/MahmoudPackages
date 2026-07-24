# Advanced Usage

## Using the Python API directly

The CLI and pytest plugin are thin wrappers around a plain Python API —
use it directly for custom tooling (a Slack bot, a dashboard, a
non-pytest test runner):

```python
from drf_contract_test import compare_schemas, generate_schema, load_schema_file

baseline = load_schema_file("openapi-baseline.yaml")
current = generate_schema(settings_module="myproject.settings")
diff = compare_schemas(baseline, current)

for change in diff.breaking_changes:
    notify_slack(f"BREAKING: {change.operation} - {change.message}")
```

## Filtering which operations to compare

`compare_schemas()` compares every operation present in either schema.
If you only care about a subset (e.g. only public, versioned endpoints),
filter both schemas' `raw["paths"]` before wrapping them in `Schema`:

```python
from drf_contract_test import Schema

def only_public(raw: dict) -> dict:
    return {
        **raw,
        "paths": {p: v for p, v in raw["paths"].items() if p.startswith("/api/v1/")},
    }

diff = compare_schemas(Schema(only_public(baseline.raw)), Schema(only_public(current.raw)))
```

## Validating live responses against the contract

`generate_contract_cases()` + `validate_response_against_schema()` let
you assert that what your API *actually returns* matches what it
*documents*, independent of the baseline-comparison workflow:

```python
import pytest
from rest_framework.test import APIClient
from drf_contract_test import generate_contract_cases, validate_response_against_schema

@pytest.mark.parametrize("case", generate_contract_cases(schema, statuses={"200"}))
def test_response_matches_contract(case, api_client: APIClient):
    response = api_client.get(case.path)
    violations = validate_response_against_schema(
        case, status_code=response.status_code, data=response.json(), root=schema.raw
    )
    assert not violations, violations
```

This catches the opposite class of bug from `compare_schemas()`: not
"did the schema change unexpectedly," but "does the code actually match
the schema it currently documents."

## Custom severity handling

`DiffResult.changes` is a plain tuple of `Change` objects — build your
own policy on top instead of relying on `has_breaking_changes`:

```python
# Treat response `enum_value_added` specially: log it, but don't fail CI,
# since your clients are documented to ignore unknown enum values.
hard_failures = [
    c for c in diff.breaking_changes if c.kind != "enum_value_added"
]
assert not hard_failures
```

## Programmatic version-bump enforcement with a custom scheme

`check_version_bump()`'s `require_major_bump` assumes `MAJOR.MINOR...`
semver-like versions. For a different scheme (date-based versions,
`vYYYY.MM`), write your own check using `diff.has_breaking_changes` and
`baseline.version`/`current.version` directly instead.

See [API Reference](api-reference.md) for every public symbol.
