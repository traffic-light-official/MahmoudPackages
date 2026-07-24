# Quick Start

## 1. Generate a baseline

Run once, and commit the result:

```bash
drf-contract-test snapshot openapi-baseline.yaml --settings myproject.settings
```

## 2. Add a CI check

`.github/workflows/api-contract.yml`:

```yaml
name: API Contract

on:
  pull_request:
    branches: [main]

jobs:
  contract:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[test]"
      - name: Check API contract
        run: |
          drf-contract-test check openapi-baseline.yaml \
            --settings myproject.settings \
            --format json --output contract-report.json
      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: contract-report
          path: contract-report.json
```

`check` exits `1` if breaking changes are present without a version
bump, failing the pull request. Use `compare` instead if you only want a
report without blocking merges.

## 3. Update the baseline when you release

After a version bump lands (and `check` passes), regenerate the baseline
so it reflects the new shape as the reference point going forward:

```bash
drf-contract-test snapshot openapi-baseline.yaml --settings myproject.settings
git add openapi-baseline.yaml
git commit -m "chore: update API contract baseline for vX.Y.Z"
```

## 4. Use it from pytest instead of the CLI

```python
# conftest.py or a dedicated test_contract.py
def test_no_undocumented_breaking_changes(contract_diff):
    assert not contract_diff.has_breaking_changes, "\n".join(
        c.message for c in contract_diff.breaking_changes
    )
```

```bash
pytest --contract-baseline=openapi-baseline.yaml --contract-settings=myproject.settings
```

See [Testing](testing.md) for the full fixture reference and
[Common Patterns](common-patterns.md) for more CI recipes.
