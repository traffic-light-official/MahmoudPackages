# Settings

This package has no Django settings - it is configured entirely through
CLI flags (or the equivalent Django management command options). This
page is the complete reference for both.

## `drf-changelog-generator diff` CLI options

### `--old-file` / `--new-file`

- **Type:** path
- One or both required if `--repo` is not used.

Paths to two local schema files (JSON or YAML, auto-detected).

### `--repo`

- **Type:** path

Path to a Git repository. Requires `--old-ref`, `--new-ref`, and
`--schema-path` together; mutually exclusive with `--old-file`/`--new-file`.

### `--old-ref` / `--new-ref`

- **Type:** str

Git refs (tags, branches, or commit SHAs) to read `--schema-path` from,
via `git show <ref>:<path>` (with `--repo`).

### `--schema-path`

- **Type:** str

Path to the schema file, relative to the repository root (with `--repo`).

### `--format`

- **Type:** `markdown` | `html` | `slack` | `github`
- **Default:** `markdown`

Output format.

### `--output`

- **Type:** path
- **Default:** `None` (prints to stdout)

Write the rendered changelog to this file instead of stdout.

### `--repo-slug`

- **Type:** str
- **Default:** `None`

`"owner/name"`, used to build a "Full API Diff" compare link in
`--format github` output.

### `--slack-webhook`

- **Type:** str (URL)
- **Default:** `None`

When set with `--format slack`, POSTs the rendered blocks to this Slack
incoming webhook URL, in addition to printing/writing them.

### `--fail-on-breaking`

- **Type:** flag
- **Default:** off

Exit with status `1` if any breaking change was detected.

## `generate_changelog` management command options

Mirrors the CLI's `--old-ref`, `--schema-path`, `--repo`, `--format`
(`markdown`/`html`/`github` only - no `slack`, since posting from a
management command context is uncommon; use the CLI directly if you
need it), `--repo-slug`, `--output`, and `--fail-on-breaking`. The
"new" version is always the current working tree, generated via
`drf-spectacular`'s own `spectacular` management command - there is no
`--new-ref` equivalent.
