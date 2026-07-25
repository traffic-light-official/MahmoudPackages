# drf-changelog-generator

Generate a changelog by diffing two OpenAPI schema versions - detecting
breaking changes, added/removed/deprecated endpoints, and field-level
request/response changes - and render it as Markdown, HTML, Slack Block
Kit, or GitHub Release notes.

```bash
drf-changelog-generator diff --old-file old.yml --new-file new.yml
```

## Why this exists

Reviewing a raw OpenAPI schema diff by eye to answer "did we just break
someone's integration" does not scale, and most teams don't do it
consistently. This package turns that diff into an explicit,
documented breaking/non-breaking classification and a changelog format
ready for a PR description, a Slack channel, or a GitHub Release - used
as a CI gate, not just documentation.

## Where to go next

- New to the package? Start with [Getting Started](getting-started.md).
- Setting it up in CI? See [Installation](installation.md) and the
  [GitHub Action](advanced-usage.md#github-action).
- Want the exact breaking-change rules? Read [Architecture](architecture.md).
- Looking for a specific function? Jump to [API Reference](api-reference.md).
- Something not behaving as expected? Check [Troubleshooting](troubleshooting.md)
  and the [FAQ](faq.md).

## At a glance

| Task | Where |
| --- | --- |
| Diff two schema files | [`diff_schemas`](api-reference.md#diff_schemas) |
| Diff two Git tags | [`load_schema_at_ref`](api-reference.md#load_schema_at_ref) |
| Render Markdown/HTML/Slack/GitHub | [`rendering`](api-reference.md#rendering) |
| Gate CI on breaking changes | `--fail-on-breaking` / [CLI](getting-started.md) |
| Wire into GitHub Actions | [`action.yml`](advanced-usage.md#github-action) |
| Wire into an existing Django project | [`generate_changelog`](advanced-usage.md#django-management-command) |
