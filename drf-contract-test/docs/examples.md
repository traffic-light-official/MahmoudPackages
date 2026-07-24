# Examples

Runnable scripts live in [`examples/`](https://github.com/mahmoudgshaker/drf-contract-test/tree/main/examples)
in the repository. This page walks through the same scenarios inline.

## Comparing two schema files

```python
# examples/compare_files.py
from drf_contract_test import compare_schemas, load_schema_file
from drf_contract_test.reports import render_text

baseline = load_schema_file("openapi-baseline.yaml")
current = load_schema_file("openapi-current.yaml")

diff = compare_schemas(baseline, current)
print(render_text(diff))

if diff.has_breaking_changes:
    raise SystemExit(1)
```

## Comparing a baseline against a live Django project

```python
# examples/compare_live.py
from drf_contract_test import compare_schemas, generate_schema, load_schema_file

baseline = load_schema_file("openapi-baseline.yaml")
current = generate_schema(settings_module="myproject.settings")

diff = compare_schemas(baseline, current)
for change in diff.changes:
    print(f"{change.severity.value.upper():8s} {change.operation} - {change.message}")
```

## Enforcing a version bump

```python
# examples/enforce_version_bump.py
from drf_contract_test import check_version_bump, compare_schemas, generate_schema, load_schema_file

baseline = load_schema_file("openapi-baseline.yaml")
current = generate_schema(settings_module="myproject.settings")
diff = compare_schemas(baseline, current)

result = check_version_bump(baseline, current, diff, require_major_bump=True)
print(result.message)
raise SystemExit(0 if result.ok else 1)
```

## Generating and validating contract tests

```python
# examples/validate_live_responses.py
import pytest
from rest_framework.test import APIClient

from drf_contract_test import generate_contract_cases, generate_schema, validate_response_against_schema

schema = generate_schema(settings_module="myproject.settings")
cases = generate_contract_cases(schema, statuses={"200", "201"})


@pytest.mark.parametrize("case", cases, ids=lambda c: c.operation)
def test_response_matches_documented_contract(case, db):
    client = APIClient()
    response = getattr(client, case.method.lower())(case.path)
    violations = validate_response_against_schema(
        case, status_code=response.status_code, data=response.json(), root=schema.raw
    )
    assert not violations, violations
```

## CLI equivalents

Every example above has a CLI one-liner:

```bash
drf-contract-test compare openapi-baseline.yaml openapi-current.yaml
drf-contract-test compare openapi-baseline.yaml --settings myproject.settings
drf-contract-test check openapi-baseline.yaml --settings myproject.settings --require-major-bump
```

See [Common Patterns](common-patterns.md) for CI-specific recipes.
