# Quick Start

A complete worked example: gating a pull request on breaking API
changes, then posting a summary to Slack on release.

## In a pull request CI job

```yaml
# .github/workflows/api-changelog.yml
name: API Changelog
on:
  pull_request:

jobs:
  changelog:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # full history, needed to diff against the base branch

      - uses: MahmoudGShake/MahmoudPackages/drf-changelog-generator@master
        with:
          old-ref: ${{ github.event.pull_request.base.sha }}
          new-ref: ${{ github.event.pull_request.head.sha }}
          schema-path: api/schema.yml
          format: markdown
          output-file: api-changelog.md
          fail-on-breaking: "false"  # comment, don't block, on PRs

      - name: Comment on the PR
        uses: marocchino/sticky-pull-request-comment@v2
        with:
          path: api-changelog.md
```

This posts (and keeps updated) a sticky PR comment showing exactly what
changed in the API for that PR - reviewers see breaking changes without
reading the raw OpenAPI diff.

## Gating a release on breaking changes

```yaml
# .github/workflows/release-check.yml
on:
  push:
    tags: ["v*.*.*"]

jobs:
  check-breaking:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - id: changelog
        uses: MahmoudGShake/MahmoudPackages/drf-changelog-generator@master
        with:
          old-ref: ${{ steps.previous-tag.outputs.tag }}
          new-ref: ${{ github.ref_name }}
          schema-path: api/schema.yml
          format: github
          fail-on-breaking: "true"
```

A major-version tag (`v2.0.0` after `v1.x.x`) is expected to have
breaking changes; a patch/minor tag (`v1.2.0` after `v1.1.0`) failing
this check is a signal something needs a closer look before release.

## Posting to Slack on every merge to main

```yaml
- uses: MahmoudGShake/MahmoudPackages/drf-changelog-generator@master
  with:
    old-ref: ${{ github.event.before }}
    new-ref: ${{ github.sha }}
    schema-path: api/schema.yml
    format: slack
    slack-webhook-url: ${{ secrets.SLACK_API_CHANGES_WEBHOOK }}
    fail-on-breaking: "false"
```

## Using the Django management command instead

If you'd rather not commit a schema file and run everything through
Django directly:

```bash
python manage.py generate_changelog \
  --old-ref v1.0.0 --schema-path api/schema.yml --format github \
  --repo-slug myorg/myproject --fail-on-breaking
```

This calls `drf-spectacular`'s own `spectacular` command to generate the
*current* schema, so it always reflects the working tree - useful in a
local pre-commit check before even opening a PR.

See [Advanced Usage](advanced-usage.md) for the full GitHub Action input
reference and programmatic library usage.
