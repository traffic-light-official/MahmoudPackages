# Architecture

## The central idea: direction changes the meaning of a diff

A structural diff between two JSON Schemas tells you *that* something
changed. It cannot, by itself, tell you whether that's dangerous — that
depends on which side of an HTTP exchange the schema describes.

- A **request** schema is a contract on what the *client* may send.
  Loosening it (accepting more) can never break an existing,
  correctly-behaving client — they were already sending something that
  satisfies the old, stricter rules, which still satisfies the new,
  looser ones. Tightening it (accepting less) can: some client that used
  to succeed may now be rejected.
- A **response** schema is a contract on what the *server* promises to
  send back. Promising more (guaranteeing a field that used to be
  optional) can't break a client relying on the old, weaker guarantee —
  it still holds. Promising less (dropping a guarantee) can: some client
  relying on it will now see something it didn't expect.

`drf_contract_test.rules.Direction` is threaded through every comparison
function specifically to apply the opposite polarity depending on which
side of the contract is being examined. This is why `compare_schema_objects()`,
not a generic schema-diff library, is the core of this package — generic
diff tools have no way to know which polarity applies.

## Module layout

```
schema.py       Schema wrapper: load/dump/generate, operation lookup
rules.py        Direction-aware comparison of two schema fragments
diff.py         Walks a full OpenAPI document operation-by-operation,
                calling rules.py for each request/response pair
changes.py      Change / Severity / DiffResult data model
versioning.py   Enforces a version bump alongside breaking changes
generator.py    Builds ContractCase objects + validates live responses
reports.py      text / json / html renderers for a DiffResult
cli.py          snapshot / compare / check subcommands
pytest_plugin.py  fixtures + options wrapping the same API
```

Each layer only depends on the ones above it in this list — `cli.py` and
`pytest_plugin.py` are both thin, independent consumers of the same
`diff.py`/`generator.py`/`versioning.py` functions; neither knows about
the other.

## `$ref` resolution

drf-spectacular schemas lean heavily on `$ref` pointers into
`components.schemas` for anything model-backed — without following
those, `compare_schema_objects()` would almost never see real field-level
differences, since most interesting content lives behind a ref rather
than inline.

`rules._resolve()` follows a single `#/...`-style JSON Pointer against
the full document (external refs are treated as opaque, since this
package only ever compares two fully-generated or fully-loaded
documents, never partial fragments with external references). Because a
resolved node can itself contain another `$ref` (drf-spectacular can
produce short indirection chains), resolution recurses, bounded by
`_MAX_RESOLUTION_DEPTH` to guarantee termination even against a
malformed or adversarial document — a broken reference is treated as
opaque rather than raising, since a fragment that can't be resolved
still carries *some* information (at minimum, its `$ref` string) worth
comparing structurally rather than crashing the whole run over one bad
document.

`generator._inline_refs()` solves a related but distinct problem: it
fully *inlines* every `$ref` into a self-contained schema (no remaining
`$ref` entries at all), because `jsonschema`'s validators expect that or
a resolver registry, and inlining avoids pulling in `jsonschema`'s
`referencing`-based registry API for what is, in this package, always a
single in-memory document. Both resolvers guard against reference
cycles (a schema that transitively refers to itself, e.g. a threaded
comment model) by tracking already-expanded ref pointers on the current
path and substituting a permissive placeholder once a cycle is detected,
rather than recursing forever.

## Why breaking-change detection and contract-test generation are separate

`diff.py` answers "did the *shape* of the contract change in a way that
could break an existing client" — purely structural, and doesn't require
a running server. `generator.py` answers "does the *actual* running code
match what it currently documents" — it requires live responses. These
are orthogonal failure modes (a schema can drift from a stable
implementation just as easily as an implementation can drift from a
stable schema), so they're exposed as separate, independently-usable
functions rather than fused into one "test my API" black box.

## Version enforcement is a policy layer, not a rule

`check_version_bump()` deliberately never raises — it always returns a
`VersionCheckResult`, because "was the version bumped" is a project
policy decision (some teams require major-only bumps for breaking
changes, others any bump, others none at all pre-1.0), not a structural
fact about the schema. Keeping it a pure function returning a result
object (rather than an assertion or exception) lets both the CLI and the
pytest plugin apply it, decide what to do with `.ok`, and render it
alongside the diff in the same report.
