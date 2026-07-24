# Common Patterns

## Block merges on breaking changes, but not on version-bump policy

Some teams want breaking changes flagged without enforcing a version
bump (e.g. pre-1.0, or an internal-only API). Use `compare` instead of
`check`:

```bash
drf-contract-test compare openapi-baseline.yaml --settings myproject.settings
```

## Report but never fail the build

Useful while first introducing the tool, before the team has agreed on
a baseline workflow:

```bash
drf-contract-test check openapi-baseline.yaml --settings myproject.settings \
  --no-fail-on-breaking --format html --output contract-report.html
```

## Per-service baselines in a monorepo

Each service gets its own baseline file and its own CI job:

```bash
drf-contract-test snapshot services/billing/openapi-baseline.yaml --settings billing.settings
drf-contract-test snapshot services/orders/openapi-baseline.yaml --settings orders.settings
```

## Treat one category of change as non-breaking

Your team may decide, for example, that new enum values in responses
are always acceptable for your clients (they're documented to ignore
unknown values) even though this package classifies them as `BREAKING`
by default. Post-process the diff:

```python
from drf_contract_test import compare_schemas
from drf_contract_test.changes import Severity

diff = compare_schemas(baseline, current)
real_breaks = [
    c for c in diff.breaking_changes if c.kind != "enum_value_added"
]
if real_breaks:
    raise SystemExit(1)
```

## Comment on pull requests with the diff

```yaml
- name: Generate contract report
  run: drf-contract-test compare openapi-baseline.yaml --settings myproject.settings --format json --output report.json --no-fail-on-breaking
- name: Post PR comment
  uses: actions/github-script@v7
  with:
    script: |
      const fs = require('fs');
      const report = JSON.parse(fs.readFileSync('report.json', 'utf8'));
      const body = report.changes.map(c => `- **${c.severity.toUpperCase()}** ${c.operation}: ${c.message}`).join('\n') || 'No changes.';
      github.rest.issues.createComment({
        issue_number: context.issue.number,
        owner: context.repo.owner,
        repo: context.repo.repo,
        body,
      });
```

## Combine with contract-test generation for full coverage

`compare_schemas()` catches schema drift between releases;
`generate_contract_cases()` + `validate_response_against_schema()` catch
drift between the schema and the running code *right now*. Run both in
CI for complete coverage — see [Advanced Usage](advanced-usage.md).
