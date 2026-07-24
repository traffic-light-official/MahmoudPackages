# Security

## Threat model

Tools registered via `@expose_as_tool` are, by definition, an API surface
you are choosing to make callable by an LLM — potentially one acting on
instructions from untrusted user input (prompt injection is a real
concern for any tool-using agent). This package's security posture:

1. **Nothing is exposed implicitly.** Every tool requires an explicit
   `actions=[...]` entry in `@expose_as_tool`. There is no "expose
   everything on this viewset" mode, and no auto-discovery of viewsets —
   you always know exactly what surface area a given registry grants.
2. **Real permission enforcement, not a parallel system.** `execute_tool`
   dispatches through the viewset's actual `.as_view()`, so
   `permission_classes` and `authentication_classes` are enforced exactly
   as they would be for a genuine HTTP request — there is no separate,
   potentially-weaker authorization path for tool calls. See
   [`ENFORCE_PERMISSIONS`](settings.md#enforce_permissions) if you ever
   need to reason about disabling this (strongly discouraged).
3. **The calling identity is explicit, never implicit.** `execute_tool`
   requires you to pass `user=` (or accepts the anonymous default) — there
   is no ambient "current user" magically picked up from thread-local
   state, which avoids an entire class of bugs where a tool call
   accidentally executes as the wrong identity.
4. **Validation is real serializer validation.** Arguments passed to
   `create`/`update`/`partial_update` tools are validated by the actual
   serializer class, with the same field-level validators, `validate_*`
   methods, and `validate()` cross-field checks a normal request would go
   through. An LLM cannot bypass validation logic by constructing
   unusual argument shapes — invalid input raises `ToolValidationError`
   exactly as a `400 Bad Request` would for a normal client.
5. **Schema generation never leaks write-only or unmapped data.** Input
   schemas only ever include fields DRF itself considers writable for
   that action; `FileField`/`ImageField` are excluded outright (see
   [Troubleshooting](troubleshooting.md)) rather than guessed at in a way
   that might expose more than intended.

## Prompt injection is out of scope, deliberately

This package secures the *tool-calling boundary* (schema accuracy,
permission enforcement, validation) — it has no way to know whether an
LLM's decision to call a particular tool with particular arguments was
influenced by adversarial content in its context window. That is a
model/agent-framework concern. What this package guarantees is that *even
if* an LLM is convinced to attempt something it shouldn't, it cannot do
anything the calling identity's permissions and the serializer's
validation wouldn't already allow a normal API client to do.

## Recommendations

- **Scope agent identities tightly.** Prefer a dedicated service account
  with the minimum permission set a given agent needs, rather than
  running tool calls as a superuser or as an arbitrary end user without
  review.
- **Never disable `ENFORCE_PERMISSIONS` for an internet-facing agent.**
  It exists specifically for closed, fully-trusted internal execution
  contexts (e.g. a background job you control end-to-end) that perform
  their own authorization before calling `execute_tool`.
- **Keep destructive actions (`destroy`, bulk-affecting custom actions)
  out of autonomous tool sets** unless you have a human-in-the-loop
  confirmation step — see [Common Patterns](common-patterns.md#human-in-the-loop-confirmation-before-destructive-tools).
- **Audit tool calls.** Nothing is logged by this package by default —
  wrap `execute_tool` at your call site if you need an audit trail (see
  [Common Patterns](common-patterns.md#auditing-every-tool-call)).

## Reporting a vulnerability

See [SECURITY.md](https://github.com/mahmoudgshaker/drf-llm-gateway/blob/main/SECURITY.md).
