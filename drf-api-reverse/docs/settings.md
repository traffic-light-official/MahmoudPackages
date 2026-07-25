# Settings

This package has no Django settings - it is configured entirely through
CLI flags (or the equivalent Django management command options). This
page is the complete reference for both.

## `drf-api-reverse scaffold` CLI options

### `--schema`

- **Type:** path, required

Path to a JSON or YAML OpenAPI document.

### `--output`

- **Type:** path, required

Directory to write `serializers.py`/`views.py`/`urls.py` into. Created
if it does not already exist. If any of the three files already exist,
they are idempotently merged with rather than overwritten - see
[Architecture](architecture.md).

## `drf-api-reverse check` CLI options

### `--schema`

- **Type:** path, required

Path to a JSON or YAML OpenAPI document - the *current* contract to
check the generated code against.

### `--output`

- **Type:** path, required

Directory previously scaffolded into. If any of the three files is
missing entirely, it is reported as drifted.

## `scaffold_api` management command options

Mirrors the CLI: `--schema`, `--output`, both required. Add `--check`
to run in check mode instead of scaffold mode (equivalent to the CLI's
separate `check` subcommand) - raises `CommandError` if drift is found,
same as any other failing management command.

```bash
python manage.py scaffold_api --schema api/contract.yml --output myapp/
python manage.py scaffold_api --schema api/contract.yml --output myapp/ --check
```
