# FAQ

## Does this replace drf-spectacular?

No — it depends on it. drf-spectacular generates the OpenAPI schema;
`drf-contract-test` compares two of them and tells you what changed and
whether it's safe. You need a working drf-spectacular setup already.

## Why is a new required response field marked SAFE but a new required request field marked BREAKING?

Because they affect compatibility in opposite ways. A new required
*response* field only adds a stronger guarantee — no existing client
relying on the old, weaker contract can be broken by getting *more* than
it expected. A new required *request* field can reject requests that
used to succeed. See [Architecture](architecture.md) for the full
reasoning.

## My schema uses OpenAPI 3.0's `nullable: true` — is that supported?

Yes. Both `nullable: true` (3.0-style) and `type: [X, "null"]` (3.1-style)
are recognized identically by `_is_nullable()`/`_base_type()`.

## Can I compare schemas from tools other than drf-spectacular?

Yes — `load_schema_file()` and `Schema()` accept any valid OpenAPI 3.0/3.1
document, regardless of what generated it. Only `generate_schema()`
(live generation from a running Django project) is drf-spectacular-specific.

## Why does `check` behave differently from `compare` when there ARE breaking changes?

`compare` only asks "are there breaking changes." `check` asks "are
there breaking changes *without* an accompanying version bump" — if you
bumped your version to acknowledge the break, `check` passes even though
breaking changes exist. Use `compare` if you want to always flag
breaking changes regardless of versioning; use `check` if bumping the
version is how your team signals "yes, this is intentional."

## Does this work with API versioning schemes like `/api/v1/`, `/api/v2/`?

Yes — each versioned path is just a distinct operation
(`GET /api/v1/articles/` vs. `GET /api/v2/articles/`); they're compared
independently. There's no special-casing needed.

## Why didn't `contract_baseline` run my test — it just says "skipped"?

You didn't pass `--contract-baseline=PATH`. This is deliberate: local
development often doesn't have a baseline checked out yet, so the plugin
skips rather than fails. See [Testing](testing.md).

## Can I use this without pytest?

Yes — the CLI (`drf-contract-test compare`/`check`) and the plain Python
API (`compare_schemas()`, etc.) don't depend on pytest at all. The
pytest plugin is an additional, optional integration point.

## Is there a GitHub Action I can use directly?

Not a published one yet — wire the CLI into a workflow step directly
(see [Quick Start](quickstart.md)); this is a thin, one-command
integration since the CLI already returns the right exit code for CI.
