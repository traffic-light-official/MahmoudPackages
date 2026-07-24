# Settings Reference

Every CLI flag and pytest-plugin option, in one place.

## CLI: `snapshot`

```
drf-contract-test snapshot <output> [--settings MODULE] [--urlconf MODULE]
```

| Argument | Description |
|---|---|
| `output` (positional) | Path to write the schema to. `.json` writes JSON; anything else writes YAML. |
| `--settings` | Dotted path to the Django settings module. |
| `--urlconf` | Dotted path to the URLconf to generate the schema from. |

## CLI: `compare` and `check`

```
drf-contract-test compare <baseline> [current] [options]
drf-contract-test check    <baseline> [current] [options]
```

| Argument | Description |
|---|---|
| `baseline` (positional) | Path to the baseline schema file. |
| `current` (positional, optional) | Path to the current schema file. If omitted, generated live via `--settings`/`--urlconf`. |
| `--settings` | Dotted path to the Django settings module (used when `current` is omitted). |
| `--urlconf` | Dotted path to the URLconf (used when `current` is omitted). |
| `--format` | Report format: `text` (default), `json`, or `html`. |
| `--output` | Write the report to this path instead of stdout. |
| `--no-fail-on-breaking` | Exit `0` regardless of what's found. Default: exit non-zero on any breaking change (`compare`) or on a failed version-bump check (`check`). |

`check` additionally accepts:

| Argument | Description |
|---|---|
| `--require-major-bump` | Require the *major* version component specifically to increase, not just the version string to differ. |

## Pytest plugin options

| Option | Description |
|---|---|
| `--contract-baseline=PATH` | Path to a baseline schema snapshot. Required for the `contract_baseline`/`contract_diff` fixtures — tests requesting them are skipped if it's not given. |
| `--contract-settings=MODULE` | Dotted path to the Django settings module for the `contract_schema` fixture. |
| `--contract-urlconf=MODULE` | Dotted path to the URLconf for the `contract_schema` fixture. |
| `--contract-require-major-bump` | Passed through to the `contract_version_check` fixture's `check_version_bump()` call. |

## Pytest plugin fixtures

| Fixture | Scope | Description |
|---|---|---|
| `contract_schema` | session | The live schema, generated via `generate_schema()`. |
| `contract_baseline` | session | The baseline schema loaded from `--contract-baseline`; skips the test if not given. |
| `contract_diff` | session | `compare_schemas(contract_baseline, contract_schema)`. |
| `contract_version_check` | session | `check_version_bump(contract_baseline, contract_schema, contract_diff, require_major_bump=...)`, honoring `--contract-require-major-bump`. |
| `contract_cases` | session | `generate_contract_cases(contract_schema)` — one `ContractCase` per documented response. |

## Python API configuration points

There is no module-level configuration object. Every function takes its
inputs explicitly:

- `generate_schema(*, settings_module=None, urlconf=None)`
- `check_version_bump(baseline, current, diff, *, require_major_bump=False)`
- `generate_contract_cases(schema, *, statuses=None)`

See [API Reference](api-reference.md) for the complete signatures.
