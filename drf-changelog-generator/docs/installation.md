# Installation

## Requirements

- Python 3.10, 3.11, 3.12, or 3.13
- `git` available on `PATH` (only needed for `--repo`/Git-ref based
  diffing; comparing two local files needs nothing but Python)
- Django 4.2+ and Django REST Framework 3.14+ (declared dependencies for
  the optional `generate_changelog` management command; not required to
  use the CLI or library directly)

## Base install

```bash
pip install drf-changelog-generator
```

## Optional extras

```bash
# Needed for the `generate_changelog` management command
pip install drf-spectacular
```

## As a GitHub Action

No `pip install` step needed in your own workflow - reference the
action directly:

```yaml
- uses: MahmoudGShake/MahmoudPackages/drf-changelog-generator@master
  with:
    old-ref: ${{ github.event.before }}
    new-ref: ${{ github.sha }}
    schema-path: api/schema.yml
```

See [Advanced Usage](advanced-usage.md#github-action) for every input.

## Verifying the install

```bash
python -c "import drf_changelog_generator; print(drf_changelog_generator.__version__)"
drf-changelog-generator --help
```

## Next steps

Continue to [Getting Started](getting-started.md) for the first diff,
or [Configuration](configuration.md) for CLI/CI wiring options.
