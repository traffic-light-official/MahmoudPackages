# Common Patterns

## Gating a PR on breaking API changes

Run the diff against the target branch's committed schema and fail the
job if anything breaking is found - the exact pattern
[`action.yml`](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-changelog-generator/action.yml)
wraps:

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0  # need full history to read old refs

- uses: MahmoudGShake/MahmoudPackages/drf-changelog-generator@master
  with:
    old-ref: origin/main
    new-ref: HEAD
    schema-path: api/schema.yml
    fail-on-breaking: "true"
```

`fetch-depth: 0` matters: `git show <ref>:<path>` needs the historical
commit to actually be present locally, and GitHub Actions' default
shallow checkout (`fetch-depth: 1`) only has the current commit.

## Posting a changelog to Slack on release

```yaml
on:
  release:
    types: [published]

jobs:
  announce:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: MahmoudGShake/MahmoudPackages/drf-changelog-generator@master
        with:
          old-ref: HEAD~1
          new-ref: ${{ github.ref_name }}
          schema-path: api/schema.yml
          format: slack
          slack-webhook-url: ${{ secrets.SLACK_CHANGELOG_WEBHOOK }}
          fail-on-breaking: "false"
```

Set `fail-on-breaking: "false"` here - a release announcement should
still post even if it happens to include breaking changes; use a
separate PR-time job (see above) to actually block a breaking merge.

## Attaching the changelog to a GitHub Release body

```yaml
- id: changelog
  uses: MahmoudGShake/MahmoudPackages/drf-changelog-generator@master
  with:
    old-ref: ${{ github.event.release.target_commitish }}
    new-ref: ${{ github.ref_name }}
    schema-path: api/schema.yml
    format: github
    repo-slug: ${{ github.repository }}

- uses: softprops/action-gh-release@v2
  with:
    body_path: ${{ steps.changelog.outputs.changelog-path }}
```

## Running the management command in a pre-commit hook

Catch a breaking change before it is even committed, by diffing the
working tree's schema against the last commit on `main`:

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: api-changelog-check
      name: Check for breaking API changes
      entry: python manage.py generate_changelog --old-ref main --schema-path api/schema.yml --fail-on-breaking
      language: system
      pass_filenames: false
      stages: [pre-push]
```

`stages: [pre-push]`, not the default `pre-commit`, since the check
needs `main` to be reachable and the working tree's migrations/schema
to be fully consistent - both are more reliably true at push time than
mid-commit.

## Diffing a live API against its own history

No local schema file is required at all - fetch both versions over
HTTP and diff the resulting dicts directly:

```python
import requests

from drf_changelog_generator import diff_schemas, render_markdown

old = requests.get("https://api.example.com/v1/schema/", timeout=10).json()
new = requests.get("https://api.example.com/v2/schema/", timeout=10).json()

diff = diff_schemas(old, new)
print(render_markdown(diff, old_ref="v1", new_ref="v2"))
```

## Failing loudly instead of gating with an exit code

If you'd rather raise in your own tooling than parse a subprocess exit
code, call the library directly:

```python
from drf_changelog_generator import diff_schemas, load_schema_file


class BreakingAPIChangeError(Exception):
    pass


old = load_schema_file("schema-old.yml")
new = load_schema_file("schema-new.yml")
diff = diff_schemas(old, new)

if diff.has_breaking_changes:
    summary = "\n".join(f"- {c.operation_label}: {c.message}" for c in diff.breaking_changes)
    raise BreakingAPIChangeError(f"Breaking API changes detected:\n{summary}")
```

## Ignoring a specific, deliberate breaking change

There is no built-in suppression list - a breaking change is a breaking
change regardless of intent. Filter `SchemaDiff.changes` yourself before
rendering if a specific, reviewed break should not gate a release:

```python
from drf_changelog_generator import diff_schemas
from drf_changelog_generator.changes import SchemaDiff

diff = diff_schemas(old, new)
approved_path = "/articles/{id}/legacy-export/"
filtered = SchemaDiff(
    changes=[c for c in diff.changes if c.path != approved_path]
)
```

Keep this narrow (one specific `path`, not a broad filter) and delete
the filter once the deprecation window for that endpoint has fully
elapsed.
