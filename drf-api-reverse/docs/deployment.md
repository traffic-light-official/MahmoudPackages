# Deployment

This package has no runtime component to deploy - it runs as a CLI
step in CI, a pre-commit hook, or a one-off developer command.
"Deployment" here means wiring it correctly into your development and
CI workflow.

## Checklist

- [ ] The generated `serializers.py`/`views.py`/`urls.py` are committed
      to version control like any other source file - this package
      does not persist any state of its own between runs; the
      generated files *are* the state.
- [ ] A CI job runs `drf-api-reverse check` (or
      `manage.py scaffold_api --check`) against the committed contract,
      failing the build if the committed generated code has drifted -
      see [Common Patterns](common-patterns.md#gating-a-pr-on-contract-drift).
- [ ] Contributors run `scaffold` locally and commit the result *before*
      opening a PR, rather than relying on CI to generate it for them -
      this package has no "auto-commit the regenerated files" mode by
      design, since a generated diff should be reviewable in the same
      PR as the contract change that caused it.
- [ ] Hand-written logic lives outside generated regions (see
      [Common Patterns](common-patterns.md#delegating-generated-method-bodies-to-real-logic-immediately)),
      so regeneration never has a chance to silently discard it.

## Wiring into an existing CI pipeline

```yaml
# .github/workflows/ci.yml
- run: pip install drf-api-reverse
- run: drf-api-reverse check --schema api/contract.yml --output myapp/
```

No Git history or checkout depth is required (unlike
`drf-changelog-generator`) - `check` only ever compares the given
schema file against the given directory's current contents, both
already present in a normal checkout.

## Versioning the contract alongside the generated code

Commit `api/contract.yml` and the generated files in the same commit
whenever either changes - `check` has no concept of "the contract as of
a previous commit," so keeping them in sync is a repository convention
this package helps enforce (via `check` failing when they diverge), not
something it manages for you.

## Running entirely offline / air-gapped

Both `scaffold` and `check` need only a local schema file and a local
output directory - no network access, no subprocess, no database (see
[Security](security.md#no-secrets-no-network-access-no-database)).
`pip install drf-api-reverse` itself is the only step requiring network
access, and can be satisfied from an internal package index like any
other dependency.
