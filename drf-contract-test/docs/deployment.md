# Deployment

`drf-contract-test` is a development/CI tool — it is not deployed
alongside your application, and adds no runtime dependency to your
production Django process. Nothing here needs to run in production;
this page covers wiring it into your release pipeline.

## Where it runs

- **Locally**, ad hoc, while developing (`compare`).
- **In CI**, on every pull request (`check`), to gate merges.
- **At release time**, to regenerate the baseline (`snapshot`) once a
  version bump has shipped.

## A minimal release pipeline

```yaml
name: Release

on:
  push:
    tags: ["v*.*.*"]

jobs:
  contract-baseline:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[test]"
      - name: Regenerate contract baseline
        run: drf-contract-test snapshot openapi-baseline.yaml --settings myproject.settings
      - name: Commit updated baseline
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add openapi-baseline.yaml
          git diff --staged --quiet || git commit -m "chore: update API contract baseline for ${{ github.ref_name }}"
          git push
```

## Ordering relative to your own release workflow

Regenerate the baseline **after** your own package/release build
succeeds, not before — if the release fails partway, you don't want a
baseline update committed for a version that was never actually
published.

## Multi-environment / multi-service considerations

If you run multiple deployable services from one repository, snapshot
and check each service's schema independently (see
[Common Patterns](common-patterns.md#per-service-baselines-in-a-monorepo)) —
there's no cross-service coordination logic in this package; each
`Schema` is independent.

## No infrastructure to provision

There's no server, database, or cache for this package to run against —
`snapshot`/`compare`/`check` only need read access to your Django
project's code and settings (to generate a schema) and to the baseline
file (to load one). Nothing here needs its own deployment target.
