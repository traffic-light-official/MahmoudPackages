# Settings

All configuration lives under a single Django setting, `LLM_GATEWAY`, a
dict of overrides merged on top of the defaults below. Settings are
validated eagerly (on first access) and cached; the cache is invalidated
automatically by Django's `setting_changed` signal, so
`@override_settings(LLM_GATEWAY={...})` works correctly in tests.

Any key not listed below raises `django.core.exceptions.ImproperlyConfigured`
the first time a setting is read.

## NAME_SEPARATOR

- **Type:** `str`
- **Default:** `"_"`

Separator used to build a tool's default name from a viewset's base name
and action, e.g. `"article" + "_" + "list"` -> `"article_list"`. Must be
non-empty.

## MAX_ENUM_VALUES

- **Type:** `int`
- **Default:** `100`

Maximum number of values inlined into a `ChoiceField`'s generated
`"enum"` list. Choice fields with more options fall back to a plain
`{"type": "string"}` schema (with an explanatory description) to avoid
enormous generated schemas.

## MAX_SCHEMA_DEPTH

- **Type:** `int`
- **Default:** `8`

Maximum recursion depth when converting nested serializers to JSON
Schema. Protects against runaway recursion from an accidentally
self-referential serializer; exceeding it raises
`SchemaGenerationError`.

## INCLUDE_EXAMPLES_IN_SCHEMA

- **Type:** `bool`
- **Default:** `True`

When `True`, examples attached via `@expose_as_tool(examples=...)` are
embedded in the generated JSON Schema under an `"examples"` key. When
`False`, examples remain available on the `ToolDefinition` object but are
omitted from the generated schema (useful if you want examples for your
own tooling but not to spend an LLM's context budget on them).

## ENFORCE_PERMISSIONS

- **Type:** `bool`
- **Default:** `True`

When `True` (default), `execute_tool()` dispatches through the real
viewset's `.as_view()`, so its `permission_classes` are enforced exactly
as they would be for a genuine HTTP request. Disable only for a fully
trusted execution context that performs its own authorization before
calling `execute_tool()` — see [Security](security.md).
