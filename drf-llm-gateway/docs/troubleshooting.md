# Troubleshooting

## `ToolRegistrationError`: a tool named '...' is already registered

**Cause:** two `@expose_as_tool` registrations (possibly on two different
viewsets, or the same viewset imported twice under different module
paths) produced the same tool name.

**Fix:** pass `name_prefix=` to disambiguate one of them, or check whether
the viewset module is being imported twice (e.g. once via `urls.py` and
once via a stray direct import elsewhere) — each import re-runs the class
decorator and attempts to re-register.

## `ToolRegistrationError`: no standard or @action-decorated method named '...'

**Cause:** an action name passed to `actions=[...]` isn't one of the six
standard actions and isn't a method on the viewset decorated with DRF's
`@action`.

**Fix:** check spelling, or decorate the method with `@action(detail=...,
methods=[...])` first — see [Quick Start](quickstart.md#registering-a-custom-action).

## `ToolRegistrationError`: must be a DRF viewset

**Cause:** `@expose_as_tool` was applied to a class that isn't a
`rest_framework.viewsets.ViewSetMixin` subclass (a plain class, a
`Serializer`, an `APIView` that isn't a viewset, ...).

**Fix:** `expose_as_tool` only works on viewsets/`ModelViewSet` subclasses
— plain `APIView`s aren't supported since they have no standard
action/URL-mapping convention to introspect.

## A field doesn't appear in the generated schema

Check, in order:

1. **Is it `FileField`/`ImageField`?** These are excluded outright — an
   LLM cannot attach binary file content to a tool call. Model file
   uploads separately (e.g. a signed-URL upload flow the agent triggers
   via a different tool that returns a URL, then references that URL in a
   text field).
2. **Is it read-only, and are you generating in `mode="input"`
   (the default)?** Read-only fields only appear in `mode="output"`
   schemas. See [`serializer_to_json_schema`](api-reference.md#serializer_to_json_schema).
3. **Is it actually declared on the serializer?** `expose_as_tool` and
   `serializer_to_json_schema` can only see fields DRF itself would
   serialize — they don't introspect the model directly.

## `SchemaGenerationError`: Serializer nesting exceeds MAX_SCHEMA_DEPTH

**Cause:** a serializer graph nests deeper than
[`MAX_SCHEMA_DEPTH`](settings.md#max_schema_depth) (default 8) — almost
always either a genuinely very deep object graph, or an accidental
self-referential serializer (e.g. `CommentSerializer` nesting `replies =
CommentSerializer(many=True)` without a depth limit).

**Fix:** for a genuinely deep graph, raise `MAX_SCHEMA_DEPTH`. For a
self-referential serializer, consider exposing only a shallow
representation (e.g. `reply_count` instead of full nested `replies`) for
tool-calling purposes — deep recursive structures are rarely useful as
LLM tool-call arguments anyway.

## `ToolPermissionDeniedError` when I expected the call to succeed

`execute_tool` enforces the tool's real `permission_classes` against the
`user=` you passed. Check:

- Did you pass the right user? Omitting `user` dispatches as
  `AnonymousUser`.
- Does that user actually have the required permission
  (`IsAuthenticated`, an object-level permission, a custom permission
  class)? Test the same user against the real HTTP endpoint if unsure —
  behavior is identical by design.
- Is [`ENFORCE_PERMISSIONS`](settings.md#enforce_permissions) accidentally
  disabled somewhere in test setup, masking what would be a real 403 in
  production? (This would cause the *opposite* problem — a call
  succeeding when you expected it to fail.)

## `ToolValidationError` with confusing field names

`ToolValidationError.detail` mirrors DRF's own `ValidationError.detail`
structure exactly (a dict of field name -> list of error messages) — the
field names are the serializer's field names, not necessarily the
argument names an LLM might have guessed at. Compare against
`tool.input_json_schema()["properties"]` to see the exact expected
argument names.

## The management command says "No tools are registered"

**Cause:** the URLconf that imports your `@expose_as_tool`-decorated
viewsets wasn't loaded. `generate_llm_tools` forces `ROOT_URLCONF` (or
`--urlconf`) to import by resolving it, but if your viewsets are
registered somewhere `ROOT_URLCONF` doesn't reach (e.g. an app not
included in your URL routing at all), they never get imported.

**Fix:** pass `--urlconf` explicitly, or ensure the viewset module is
imported by something the command triggers (a router registration in a
URLconf is the most reliable trigger).
