# Troubleshooting

## `InvalidFieldsParameterError`: unbalanced parentheses

**Cause:** the `fields` expression has a `(` without a matching `)`, or
vice versa.

```
?fields=author(name,email
```

**Fix:** balance the parentheses, or check whether your HTTP client is
URL-decoding/truncating the query string unexpectedly.

## `InvalidFieldsParameterError`: cannot combine plain field names with exclusions

**Cause:** a single group mixed `name` and `-name` styles, e.g.
`?fields=id,-body`.

**Fix:** pick one style per group. Either list what you want
(`?fields=id,title`) or what you don't (`?fields=-body,-internal_notes`).

## `InvalidFieldsParameterError`: field was requested more than once

**Cause:** the same field name (or alias target) appears twice in one
group, e.g. `?fields=id,id` or `?fields=a:x,a:y`.

**Fix:** remove the duplicate. This is rejected rather than silently
deduplicated because it's almost always a client-side bug worth surfacing.

## `InvalidFieldsParameterError`: exceeds the maximum nesting depth

**Cause:** the expression nests deeper than
[`MAX_DEPTH`](settings.md#max_depth) (default 6).

**Fix:** either restructure the request, or raise `MAX_DEPTH` in
`PARTIAL_RESPONSE_FIELDS` if your models are legitimately that deeply
nested.

## A field I requested doesn't appear in the response

1. Check it's actually listed in the serializer's `Meta.fields` (or
   declared explicitly) — `?fields=` can only narrow what's already
   exposed, never add new fields.
2. Check [`STRICT`](settings.md#strict) — if disabled (the default),
   requesting a typo'd or nonexistent field name is a silent no-op. Enable
   `STRICT` temporarily to get an explicit `400` naming the unknown field.
3. Check it's not a `write_only` field — those are never included in
   output regardless of `fields=`.

## A nested field I requested still returns the full default representation

The nested serializer needs `PartialFieldsSerializerMixin` (or one of the
ready-made base classes) applied to *it specifically* — see
[FAQ](faq.md#why-do-i-need-the-mixin-on-nested-serializers-too). A plain
`serializers.ModelSerializer` nested inside a `PartialFieldsModelSerializer`
does not inherit filtering behavior.

## `?fields=` seems to have no effect on a `POST`/`PUT`/`PATCH` request

This is expected: [`SAFE_METHODS_ONLY`](settings.md#safe_methods_only)
(default `True`) ignores `fields=` entirely on unsafe methods, so both
input validation and the response always use the full field set. See
[Security](security.md) for why. If you're certain your write endpoints
don't rely on required-field validation a client could bypass, you can
disable this — but review that assumption carefully first.

## The optimizer didn't add `select_related`/`prefetch_related` for a relation I expected

The optimizer only acts when it can confidently map a serializer field to
a concrete model relation. It deliberately does *nothing* (falls back to
normal, unoptimized attribute access — correct but not optimized) for:

- **`@property` or other computed attributes** without a matching model
  field name.
- **`GenericForeignKey`** relations — there's no single "related model" to
  build a `select_related`/`prefetch_related` path for.
- **Reverse one-to-one relations exposed via `PrimaryKeyRelatedField`**
  (rather than a nested serializer) — DRF's own pk-only optimization
  assumes a forward FK's `_id` shadow attribute, which doesn't exist on the
  reverse side. Expose it via a nested serializer instead.
- **A `source` of `"*"`** (the whole-object sentinel some custom fields
  use) — there's no single attribute path to resolve.

If you need optimization for a computed field, use
[`requires_related`](advanced-usage.md#optimizing-serializermethodfield) to
declare the relations it depends on explicitly.

## I get `ImproperlyConfigured` on startup/first request

**Cause:** `PARTIAL_RESPONSE_FIELDS` in your Django settings has an unknown
key, a value of the wrong type, or an invalid `QUERY_PARAM` (must be a
valid Python identifier). The error message names the exact key and
constraint violated.

**Fix:** compare your `PARTIAL_RESPONSE_FIELDS` dict against
[Settings](settings.md) — every key must match exactly (case-sensitive)
and pass its type/value validation.

## `django.core.exceptions.FieldError` after enabling query optimization

If this happens, it means the optimizer built an `only()`/`select_related()`
call incompatible with something else in your `get_queryset()` chain (for
example, a custom `.values()` call earlier in the chain, which is
fundamentally incompatible with `.only()`). Set
[`ENABLE_QUERY_OPTIMIZATION = False`](settings.md#enable_query_optimization)
for that specific view (or override `get_queryset()` to bypass the mixin's
call) and please
[open an issue](https://github.com/mahmoudgshaker/drf-partial-response-fields/issues)
with a minimal reproduction — this is not expected behavior for normal
`ModelSerializer`/queryset usage.

## Tests fail with "no such table" against my Django test app

This package's own test suite runs with `--no-migrations` (see
`pyproject.toml`). If you're adapting patterns from
[Testing](testing.md) into a project that *does* use migrations normally,
make sure your test settings module actually runs migrations (the default
for most projects) or your test models simply won't have tables.
