# Examples

Two example schema files (`schema-v1.yml`, `schema-v2.yml`) and a small
script demonstrating the programmatic API live in
[`examples/blog/`](https://github.com/MahmoudGShake/MahmoudPackages/tree/master/drf-changelog-generator/examples/blog).

## Markdown output

```bash
drf-changelog-generator diff --old-file examples/blog/schema-v1.yml --new-file examples/blog/schema-v2.yml
```

```markdown
# API Changelog: `examples/blog/schema-v1.yml` -> `examples/blog/schema-v2.yml`

## Breaking Changes

- `GET /articles/{id}/`: Removed field 'legacy_id'

## Removed Endpoints

- `DELETE /articles/{id}/`: Removed DELETE /articles/{id}/

## Deprecated Endpoints

- `POST /articles/`: POST /articles/ is now deprecated

## Added Endpoints

- `GET /articles/{id}/comments/`: Added GET /articles/{id}/comments/

## Non-Breaking Changes

- `GET /articles/{id}/`: Added field 'tags'
```

## HTML output

```bash
drf-changelog-generator diff --old-file examples/blog/schema-v1.yml --new-file examples/blog/schema-v2.yml --format html --output changelog.html
```

Produces a single self-contained HTML file with breaking changes styled
in red - open it directly in a browser, or publish it as a build
artifact.

## Slack output

```bash
drf-changelog-generator diff --old-file examples/blog/schema-v1.yml --new-file examples/blog/schema-v2.yml --format slack
```

```json
[
  {"type": "header", "text": {"type": "plain_text", "text": "API Changelog: examples/blog/schema-v1.yml -> examples/blog/schema-v2.yml"}},
  {"type": "divider"},
  {"type": "section", "text": {"type": "mrkdwn", "text": "*:warning: Breaking Changes*\n- `GET /articles/{id}/`: Removed field 'legacy_id'"}},
  {"type": "divider"},
  {"type": "section", "text": {"type": "mrkdwn", "text": "*:x: Removed Endpoints*\n- `DELETE /articles/{id}/`: Removed DELETE /articles/{id}/"}},
  {"type": "divider"},
  {"type": "section", "text": {"type": "mrkdwn", "text": "*:hourglass: Deprecated Endpoints*\n- `POST /articles/`: POST /articles/ is now deprecated"}},
  {"type": "divider"},
  {"type": "section", "text": {"type": "mrkdwn", "text": "*:sparkles: Added Endpoints*\n- `GET /articles/{id}/comments/`: Added GET /articles/{id}/comments/"}},
  {"type": "divider"},
  {"type": "section", "text": {"type": "mrkdwn", "text": "*:information_source: Non-Breaking Changes*\n- `GET /articles/{id}/`: Added field 'tags'"}}
]
```

One `section` block is emitted per non-empty category, each preceded by a
`divider`. Paste the output into
[Slack's Block Kit Builder](https://app.slack.com/block-kit-builder) to
preview it, or pass `--slack-webhook <url>` to post it directly.

## GitHub Release notes output

```bash
drf-changelog-generator diff --old-file examples/blog/schema-v1.yml --new-file examples/blog/schema-v2.yml --format github --repo-slug myorg/myproject
```

```markdown
## :warning: Breaking API Changes

- `DELETE /articles/{id}/`: Removed DELETE /articles/{id}/
- `GET /articles/{id}/`: Removed field 'legacy_id'

## Deprecated

- `POST /articles/`: POST /articles/ is now deprecated

## Added

- `GET /articles/{id}/comments/`: Added GET /articles/{id}/comments/

## Other API Changes

- `GET /articles/{id}/`: Added field 'tags'

**Full API Diff**: https://github.com/myorg/myproject/compare/examples/blog/schema-v1.yml...examples/blog/schema-v2.yml
```

(The compare link only makes sense with real Git tags as `--old-ref`/`--new-ref`,
not local file paths - shown here for format illustration only.)

## Programmatic usage

```python
# examples/blog/generate_changelog.py
from pathlib import Path

from drf_changelog_generator import diff_schemas, load_schema_file, render_markdown

HERE = Path(__file__).parent

old = load_schema_file(HERE / "schema-v1.yml")
new = load_schema_file(HERE / "schema-v2.yml")
diff = diff_schemas(old, new)

print(f"{len(diff.breaking_changes)} breaking change(s) detected.")
print(render_markdown(diff, old_ref="v1", new_ref="v2"))
```
