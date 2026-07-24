# drf-partial-response-fields

GraphQL-like sparse fieldsets for Django REST Framework, with automatic
query optimization so that requesting fewer fields also means fewer
database queries and less data read off the wire.

```
GET /api/articles/1/?fields=title,author(name,email),tags(label)
```

## Why this exists

Most "sparse fieldset" packages for DRF stop at filtering the serializer's
*output*. They shrink the JSON payload but leave the ORM query untouched —
you still pay for every `select_related`-worthy join and every
`SerializerMethodField` computation, even for fields the client never asked
for. `drf-partial-response-fields` does both halves of the job:

1. **Output filtering** — only the requested fields (and their requested
   nested sub-fields, at any depth) appear in the response.
2. **Query optimization** — `select_related`, `prefetch_related`, and
   `only()` are derived automatically from what was requested, including
   recursively-optimized nested `Prefetch` querysets.

See [Performance](performance.md) for measured query-count reductions.

## Where to go next

- New to the package? Start with [Getting Started](getting-started.md).
- Wiring it into an existing project? See [Installation](installation.md)
  and [Configuration](configuration.md).
- Want the full picture of how it works? Read [Architecture](architecture.md).
- Looking for a specific class or setting? Jump to
  [API Reference](api-reference.md) or [Settings](settings.md).
- Something not behaving as expected? Check [Troubleshooting](troubleshooting.md)
  and the [FAQ](faq.md).

## At a glance

| Task | Where |
| --- | --- |
| Filter fields on a serializer | [`PartialFieldsSerializerMixin`](api-reference.md#partialfieldsserializermixin) |
| Wire up a view/viewset | [`PartialResponseMixin`](api-reference.md#partialresponsemixin) |
| Optimize a `SerializerMethodField` | [`requires_related`](api-reference.md#requires_related) |
| Document `?fields=` in OpenAPI | [`PartialResponseAutoSchema`](api-reference.md#partialresponseautoschema) |
| Change the query parameter name, strictness, depth limit, etc. | [Settings](settings.md) |
