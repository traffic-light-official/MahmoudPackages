# FAQ

## Does this call OpenAI/Anthropic/any LLM API for me?

No. This package only generates tool schemas in the shapes those APIs
expect, and dispatches tool calls once your own code (or an SDK like the
OpenAI Python client) has decided a tool should be called. There is no
network call to any LLM provider anywhere in this package.

## Does `execute_tool` require a real HTTP request?

No — it *constructs* one internally via `APIRequestFactory` so that your
viewset's real dispatch logic runs, but you call `execute_tool()` as a
plain Python function from wherever your agent-handling code lives
(a Celery task, a management command, a view, a websocket consumer, ...).

## Can I expose a ViewSet method that isn't a standard action or `@action`?

Not directly — `expose_as_tool` needs either a standard action name
(`list`, `create`, `retrieve`, `update`, `partial_update`, `destroy`) or a
method decorated with DRF's `@action`. If you have a plain method you want
to expose, wrap it with `@action` first; this also makes it callable over
HTTP normally, which is usually what you want anyway.

## What happens if two viewsets would generate the same tool name?

`ToolRegistry.register()` raises `ToolRegistrationError` immediately, at
import time (when the decorator runs) — not later, silently. Use
`name_prefix=` to disambiguate.

## Does this support async views?

`execute_tool` dispatches via Django's synchronous test-request machinery.
If your viewset is `async def`-based, `.as_view()` still returns a
callable Django can invoke, but `execute_tool` calls it synchronously —
for a fully async agent pipeline, wrap the call with
`asgiref.sync.sync_to_async` on the caller's side.

## Can an LLM see fields I didn't intend to expose?

Only if those fields are already part of the serializer used for that
tool's action. `serializer_to_json_schema` never includes more than the
serializer itself would output/accept. If a serializer includes a field
you don't want an agent to see, don't use that serializer class for the
tool — use `serializer_classes={"create": ScopedSerializer}` to override
per action (see [Advanced Usage](advanced-usage.md#per-action-serializer-overrides)).

## Why is `schema_hash` different from `version`?

`version` is whatever string you assign (or the default `"1.0.0"`) —
meant for a human-readable, deliberately-bumped semantic version.
`schema_hash` is computed automatically from the current schema every
time it's accessed — meant for detecting *unintentional* drift (did
someone change a field without updating `version`?). Use both together:
bump `version` for intentional, communicated changes; watch `schema_hash`
to catch the ones nobody remembered to communicate.

## Does this work with DRF's `Response` renderers (XML, etc.)?

`execute_tool` reads `response.data` (the pre-render Python object), not
the rendered bytes, so configured renderer classes are irrelevant to tool
results — you always get plain Python data (dicts/lists/primitives), ready
to hand to an LLM or JSON-encode yourself.

## Is there a GraphQL equivalent?

Not from this package specifically — see `drf-partial-response-fields` in
the same family of packages if you want GraphQL-style field selection over
plain REST responses; that's a different problem (over-fetching) from
tool-calling schema generation.
