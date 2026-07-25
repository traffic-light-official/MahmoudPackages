# Configuration

Unlike most packages in this workspace, `drf-changelog-generator` has no
Django settings - every option is a CLI flag (or a Django management
command option, for the optional `generate_changelog` wrapper). See
[Settings](settings.md) for the full reference.

## Comparing two local files

```bash
drf-changelog-generator diff --old-file old.yml --new-file new.yml
```

## Comparing two Git refs

```bash
drf-changelog-generator diff \
  --repo /path/to/project \
  --old-ref v1.0.0 --new-ref v1.1.0 \
  --schema-path api/schema.yml
```

`--repo` requires `--old-ref`, `--new-ref`, and `--schema-path` together;
mixing `--old-file`/`--new-file` with `--repo` is not supported (they
address two different sources for the same two schema versions).

## Choosing an output format

```bash
--format markdown   # default
--format html
--format slack
--format github --repo-slug myorg/myproject
```

## Writing to a file instead of stdout

```bash
--output CHANGELOG.md
```

## Posting to Slack directly

```bash
--format slack --slack-webhook https://hooks.slack.com/services/...
```

Still prints the rendered JSON blocks to stdout/`--output` as well as
posting them - use `--output /dev/null` (or discard stdout) if you only
want the Slack post.

## Failing CI on breaking changes

```bash
--fail-on-breaking
```

Exit code `1` if any breaking change was found, `0` otherwise (or `2`
for a usage/loading error, e.g. an unknown Git ref).

## Django management command

For projects already using `drf-spectacular`:

```bash
python manage.py generate_changelog --old-ref v1.0.0 --schema-path api/schema.yml
```

Diffs the schema `drf-spectacular` generates for the *current* working
tree against the schema committed at `--old-ref`. See
[Advanced Usage](advanced-usage.md#django-management-command).
