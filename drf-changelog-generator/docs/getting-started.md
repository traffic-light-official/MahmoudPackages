# Getting Started

## 1. Install

```bash
pip install drf-changelog-generator
```

This installs the `drf-changelog-generator` console script - no Django
project is required to use it.

## 2. Get two schema versions

You need an OpenAPI schema (JSON or YAML) for each version you want to
compare. If your project uses `drf-spectacular`:

```bash
python manage.py spectacular --file schema.yml
```

Commit `schema.yml` to your repository on every release so past versions
remain available via `git show <tag>:schema.yml`.

## 3. Diff two local files

```bash
drf-changelog-generator diff --old-file old-schema.yml --new-file new-schema.yml
```

```markdown
# API Changelog: `old-schema.yml` -> `new-schema.yml`

## Breaking Changes

- `DELETE /articles/{id}/`: Removed field 'legacy_id'

## Added Endpoints

- `GET /articles/{id}/comments/`: Added GET /articles/{id}/comments/
```

## 4. Diff two Git tags

If `schema.yml` is committed at each tagged release:

```bash
drf-changelog-generator diff \
  --repo . --old-ref v1.0.0 --new-ref v1.1.0 \
  --schema-path schema.yml
```

No checkout happens - the file is read directly from Git history via
`git show`.

## 5. Gate CI on breaking changes

```bash
drf-changelog-generator diff \
  --repo . --old-ref v1.0.0 --new-ref HEAD \
  --schema-path schema.yml --fail-on-breaking
```

Exits with status `1` if any breaking change was detected - wire this
into a CI job to require explicit sign-off (or a major version bump)
before merging a breaking API change.

## 6. Choose an output format

```bash
drf-changelog-generator diff ... --format github --repo-slug myorg/myproject
```

`--format` accepts `markdown` (default), `html`, `slack`, or `github`.
See [Examples](examples.md) for sample output of each.

See [Quick Start](quickstart.md) for the GitHub Action and Django
management command wiring.
