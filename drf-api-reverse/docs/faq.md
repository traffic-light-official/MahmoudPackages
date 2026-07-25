# FAQ

## Why would my hand-written ViewSet logic get overwritten?

Because it was written *inside* a generated method's body, which lives
inside a marked region - `scaffold` regenerates a region's entire
content on every run, including a method's `def` line and body, as long
as the schema still produces that operation. If you write your real
implementation directly in place of `raise NotImplementedError(...)`,
it survives only until the next schema change touches that same
operation, at which point it's replaced with a fresh stub. The fix:
delegate immediately to a function defined outside any region (see
[Common Patterns](common-patterns.md#delegating-generated-method-bodies-to-real-logic-immediately)) -
that function is never regenerated, since it isn't part of what
`scaffold` produces.

## Why did an operation not get scaffolded at all?

Only three path shapes are automatically classified: a bare collection
path (`/things/`), a collection path plus one trailing `{param}`
(`/things/{id}/`), and one further literal segment after that
(`/things/{id}/history/`). Anything else - two path parameters, four or
more segments - is classified `"unsupported"` and recorded as a comment
in the generated `ViewSet` rather than silently dropped or
incorrectly generated. See the
[classification table](architecture.md#resource-grouping-and-operation-classification)
for the exact rule, and add the corresponding route/method by hand.

## What happens with a circular schema reference?

Two schemas that reference each other (`A` has a field typed `B`, `B`
has a field typed `A`) cannot both be emitted as in-order Python class
definitions - one of them must come first, and at that point the other
doesn't exist yet. The class encountered second in such a cycle gets a
plain `DictField()` in place of the nested serializer, with a comment
explaining why. There is no silent workaround (e.g. deferred/lazy field
resolution) - resolve the cycle in your contract if you need both
directions to be a real nested serializer (e.g. one direction becomes a
simple ID reference instead of a full nested object, which is standard
REST practice for cyclic relationships anyway).

## Does this package require a Django model to exist?

No - the opposite, in fact. Generated serializers are always plain
`serializers.Serializer` subclasses, never `ModelSerializer`, precisely
because a design-first contract is meant to exist *before* the model
does. Once you do have a model, migrating a specific serializer to
`ModelSerializer` is a normal hand-edit outside this package's scope -
`scaffold` will not fight you on it as long as you also remove that
serializer's own generated region markers (otherwise it will be
overwritten back to a plain `Serializer` on the next `scaffold` run for
an unrelated schema change).

## Can I use this with a schema from a non-DRF, non-Django source?

Yes for the *contract* - any spec-compliant OpenAPI 3.x document works,
regardless of what produced it (hand-written, another team's
`drf-spectacular` output, a third-party API's published spec). The
*output*, however, is always Django REST Framework code - this package
does not generate for any other framework.

## Does it support OpenAPI 2.0 / Swagger?

No - only OpenAPI 3.x's `paths`/`components.schemas` structure is
understood. Convert a 2.0 document to 3.x first if needed.

## Do I need `drf-spectacular` installed?

No, not for the core `scaffold`/`check` workflow - both take an
already-existing schema file. The `[spectacular]` extra exists only for
projects that want to combine this package with `drf-spectacular`
themselves (e.g. diffing a live project's generated schema against a
design-first contract in a custom script); nothing in this package's
own shipped CLI or management command requires it.

## Can I customize which DRF field class a JSON Schema type maps to?

Not via a setting - the mapping is a fixed, documented table (see
`type_mapping.py`) so that "what does `{"type": "string", "format":
"date-time"}` become" always means the same thing across every project
using this package. If you need a different mapping for a specific
field, generate normally and then hand-edit that one field - it lives
in the same region as the rest of the class, so a future unrelated
change to that schema will regenerate your edit away too; keep such
overrides narrow and re-apply them if that happens; or see
[Advanced Usage](advanced-usage.md#writing-your-own-generator-against-the-same-region-merge-engine)
to write a fully custom generator instead.
