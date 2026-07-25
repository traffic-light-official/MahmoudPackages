# FAQ

## Does this package generate my OpenAPI schema for me?

No, except indirectly via the optional `generate_changelog` management
command, which calls `drf-spectacular`'s own `spectacular` command to
generate the *current* schema before diffing it. The standalone CLI
always takes two already-existing schemas (two files, or two Git refs
at which a schema file was committed) - see
[Architecture](architecture.md#the-cli-has-no-django-dependency-in-its-execution-path).

## Does it support Swagger 2.0 / OpenAPI 2.0?

No - only OpenAPI 3.x's `paths`/`components.schemas` structure is
understood. Swagger 2.0's `definitions`/`parameters` top-level layout is
different enough that a 2.0 document will simply produce an empty or
incorrect diff rather than a clear error; convert to 3.x first (most
tools, including `drf-spectacular`, only emit 3.x today anyway).

## Can I diff two schemas that use external (non-local) `$ref`s?

Not currently - `diffing.refs.deref()` only resolves local `#/...` JSON
pointers within the same document (see
[Performance](performance.md#ref-resolution-is-cached-per-diff-not-per-field)).
A `$ref` to another file or a remote URL is left unresolved, and any
field diffing inside it is skipped. Bundle/dereference external refs
into a single document first (e.g. with `openapi-spec-validator` or a
similar bundler) before diffing.

## Why does the same field change sometimes show up twice?

If two different operations (or a request body and a response body of
the *same* operation) reference the same named schema (e.g. both `POST
/articles/`'s request and response use `#/components/schemas/Article`),
a field added/removed on that shared schema is reported once per
occurrence, not deduplicated - each occurrence is genuinely a different
part of the contract that a client could be relying on independently.
If this produces noisy output for your schema, consider using distinct
request/response schemas (e.g. `ArticleCreate` vs. `Article`) as shown
in [Examples](examples.md), which is standard REST API design practice
regardless of this package.

## Does `--fail-on-breaking` fail on deprecation alone?

No - `ENDPOINT_DEPRECATED`/`ENDPOINT_UNDEPRECATED` are always
non-breaking (see the [rule table](architecture.md#the-breaking-change-rule-set)).
Deprecating an endpoint is a signal for consumers to migrate away, not
an immediate behavior change; the endpoint still works exactly as
before until it is actually removed, which *is* breaking.

## Can I customize the breaking/non-breaking classification?

Not via a setting - the rule set is fixed and documented so that a
"breaking change" always means the same thing across every project
using this package (see [Architecture](architecture.md#the-breaking-change-rule-set)).
Filter `SchemaDiff.changes` yourself after diffing if a specific
category needs different treatment in your pipeline - see
[Common Patterns](common-patterns.md#ignoring-a-specific-deliberate-breaking-change).

## Does it need a live database or Django app to run?

No. `diff_schemas()`, every renderer, `schema_loader`, and `git_utils`
are pure functions with no Django dependency at import time - only the
optional `generate_changelog` management command needs a configured
Django project (to call `drf-spectacular`'s `spectacular` command).

## Can I use this with a schema from FastAPI, or any non-DRF framework?

Yes - the diff engine operates on the OpenAPI document structure itself,
not on any DRF-specific metadata. Any spec-compliant OpenAPI 3.x
document works, regardless of what generated it.

## What happens if a ref doesn't exist, or `git` isn't installed?

`GitError` is raised (a subclass of `ChangelogGeneratorError`), and the
CLI prints `Error: ...` to stderr and exits with status `2` - see
[Troubleshooting](troubleshooting.md#git-related-errors).
