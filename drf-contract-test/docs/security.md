# Security

## No code execution from schema files

Schema files are loaded with `yaml.safe_load()`, never `yaml.load()` or
`yaml.unsafe_load()` — arbitrary Python object construction via YAML
tags (`!!python/object/apply:...`) is not possible through
`load_schema_file()`. JSON schema files go through the standard library
`json.loads()`, which has no code-execution surface at all.

## Bounded `$ref` resolution

Both comparison (`rules._resolve()`) and contract-test validation
(`generator._inline_refs()`) follow `$ref` pointers within a schema
document. A maliciously crafted schema with a very deep or cyclic
reference chain cannot cause unbounded recursion or a denial-of-service
via stack exhaustion — both resolvers are bounded by a fixed maximum
depth and detect cycles explicitly, falling back to an opaque/permissive
placeholder rather than recursing further. See
[Architecture](architecture.md) for the mechanism.

## External references are never followed

A `$ref` pointing outside the current document (anything not starting
with `#/`) is left unresolved rather than fetched — this package never
makes a network request or reads an arbitrary file path found inside a
schema document. If you need multi-file schema composition, resolve
external references into a single document *before* passing it to this
package (e.g. with your OpenAPI tooling of choice).

## Response validation trusts neither side

`validate_response_against_schema()` validates a live HTTP response
against a documented schema using `jsonschema`, a pure-data validator
with no code-execution surface — it inspects your response body as data
only. Treat the response body itself as sensitive if your API returns
sensitive data (PII, tokens): validation results are the same shape of
data as your response, so redact accordingly before including them in
CI logs or PR comments if that's a concern.

## No credentials or secrets involved

This package has no notion of authentication, secrets, or credentials of
its own. Schema generation introspects your DRF configuration (views,
serializers, permission *classes* as metadata) without making any HTTP
requests or evaluating permission checks against real data. Only the
optional contract-test validation helper (`validate_response_against_schema`)
deals with live data at all, and only because *you* choose to call a
real endpoint and pass its response in — this package never initiates
that call itself.

## Reports are static, local files

`render_html()`/`render_json()`/`render_text()` produce self-contained
output with no external network calls, remote assets, or embedded
scripts beyond inline CSS in the HTML report — safe to archive as a CI
artifact or serve as a static file.

## Reporting a vulnerability

See [SECURITY.md](https://github.com/mahmoudgshaker/drf-contract-test/blob/main/SECURITY.md)
in the repository root for the disclosure process.
