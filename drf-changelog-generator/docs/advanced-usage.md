# Advanced Usage

## Using the library programmatically

Every CLI capability is a plain function:

```python
from drf_changelog_generator import diff_schemas, load_schema_file, render_markdown

old = load_schema_file("old-schema.yml")
new = load_schema_file("new-schema.yml")
diff = diff_schemas(old, new)

if diff.has_breaking_changes:
    for change in diff.breaking_changes:
        print(f"BREAKING: {change.operation_label}: {change.message}")

print(render_markdown(diff, old_ref="v1.0.0", new_ref="v1.1.0"))
```

## Diffing schemas from any source, not just files

`diff_schemas()` takes plain dicts - load them however you like (an
HTTP request to a live `/schema/` endpoint, a database snapshot, an
in-memory generation call):

```python
import requests

from drf_changelog_generator import diff_schemas

old = requests.get("https://api-v1.example.com/schema/").json()
new = requests.get("https://api-v2.example.com/schema/").json()
diff = diff_schemas(old, new)
```

## GitHub Action

The full input reference (see [`action.yml`](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-changelog-generator/action.yml)):

| Input | Default | Description |
| --- | --- | --- |
| `old-ref` | *(required)* | Git ref for the earlier schema. |
| `new-ref` | `HEAD` | Git ref for the later schema. |
| `schema-path` | *(required)* | Path to the schema file in the repo. |
| `format` | `github` | `markdown`, `html`, `slack`, or `github`. |
| `repo-slug` | `${{ github.repository }}` | Used for GitHub-format compare links. |
| `output-file` | `api-changelog.md` | Where the rendered changelog is written. |
| `fail-on-breaking` | `true` | Fail the step if breaking changes are found. |
| `slack-webhook-url` | *(none)* | Post to this Slack webhook (`format: slack` only). |

Outputs: `changelog-path` and `has-breaking-changes` (`"true"`/`"false"`),
usable in later steps:

```yaml
- id: changelog
  uses: MahmoudGShake/MahmoudPackages/drf-changelog-generator@master
  with:
    old-ref: v1.0.0
    new-ref: v1.1.0
    schema-path: api/schema.yml

- if: steps.changelog.outputs.has-breaking-changes == 'true'
  run: echo "::warning::This release includes breaking API changes."
```

## Django management command

```bash
python manage.py generate_changelog \
  --old-ref v1.0.0 --schema-path api/schema.yml \
  --format markdown --output CHANGELOG.md --fail-on-breaking
```

Requires `drf_changelog_generator` in `INSTALLED_APPS` and
`drf-spectacular` installed and configured (it calls
`call_command("spectacular", file=...)` internally to generate the
current schema into a temporary file). See
[Common Patterns](common-patterns.md#running-the-management-command-in-a-pre-commit-hook).

## Custom renderers

Every renderer is a plain function taking a `SchemaDiff` and returning a
string (or, for Slack, a list of blocks) - write your own against
`SchemaDiff`/`Change` directly if you need a format this package doesn't
ship, e.g. a JIRA-flavored wiki format:

```python
from drf_changelog_generator.changes import SchemaDiff
from drf_changelog_generator.rendering.common import summarize


def render_jira_wiki(diff: SchemaDiff, *, old_ref: str, new_ref: str) -> str:
    summary = summarize(diff)
    lines = [f"h1. API Changelog: {old_ref} -> {new_ref}"]
    if summary.other_breaking:
        lines.append("h2. Breaking Changes")
        lines.extend(f"* {c.operation_label}: {c.message}" for c in summary.other_breaking)
    return "\n".join(lines)
```

## Resolving `$ref` yourself

`diffing.refs.deref()` and `resolve_ref()` are public if you need to
inspect a schema's structure outside of diffing:

```python
from drf_changelog_generator.diffing.refs import deref

article_schema = deref(document, {"$ref": "#/components/schemas/Article"})
```
