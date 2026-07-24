# Quick Start

This page tours the `fields` mini-language and the most common usage
patterns. It assumes you've completed [Getting Started](getting-started.md).

## The `fields` mini-language

```
fields_expr  := group
group        := entry ("," entry)* | ""
entry        := "*"
entry        := "-" NAME
entry        := (NAME ":")? NAME ("(" group ")")?
NAME         := [A-Za-z_][A-Za-z0-9_]*
```

### Selecting top-level fields

```
?fields=id,title,view_count
```

Only `id`, `title`, and `view_count` appear in the response (plus anything
listed in [`ALWAYS_INCLUDE`](settings.md#always_include), which defaults to
`["id"]`).

### Nested selection

```
?fields=title,author(name,email)
```

```json
{"title": "...", "author": {"name": "Ada Lovelace", "email": "ada@example.com"}}
```

Nesting works at any depth:

```
?fields=author(company(name,address(city,country)))
```

A field requested *without* parentheses (`?fields=author`) gets its full
default representation — no sub-restriction is applied.

### Exclusion

```
?fields=-internal_notes,-legacy_id
```

Keeps every default field except the ones listed. Exclusion and inclusion
cannot be combined in the same group (`?fields=id,-body` is rejected as
ambiguous) — pick one style per group. You can still mix styles across
nesting levels: `?fields=author(-email)` inside an otherwise unrestricted
top level is fine, since `author(...)` is its own group.

### Aliasing

```
?fields=publishedAt:created_at
```

Renames the `created_at` field to `publishedAt` in the output. Works at
any nesting level:

```
?fields=author(fullName:name)
```

```json
{"author": {"fullName": "Ada Lovelace"}}
```

### Wildcards

```
?fields=*
```

Explicitly requests "no restriction" — equivalent to omitting the `fields`
parameter entirely. Mostly useful nested, to explicitly opt back into a
field's full default representation: `?fields=title,author(*)`. A lone `*`
cannot be combined with explicit names or exclusions in the same group.

## Works everywhere DRF does

### ViewSets and generic views

```python
class ArticleViewSet(PartialResponseMixin, viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
```

Every action (`list`, `retrieve`, `create`, `update`, `partial_update`,
`destroy`) is covered automatically.

### Pagination

`PartialResponseMixin` optimizes the queryset *before* pagination slices
it, so page size and query cost are independent of which fields were
requested:

```
GET /articles/?fields=title&page_size=20
```

```json
{"count": 142, "next": "...", "previous": null, "results": [{"id": 1, "title": "..."}, ...]}
```

### The Browsable API

Nothing special is required — the Browsable API renders whatever
`to_representation()` returns, so it reflects the `fields` filtering
automatically when you append `?fields=...&format=api` (or just view in a
browser with `Accept: text/html`).

### `SerializerMethodField`

Unrequested method fields are removed from the serializer's field set
*before* rendering, so their `get_<field>` method is never called:

```python
class ArticleSerializer(PartialFieldsModelSerializer):
    comment_count = serializers.SerializerMethodField()

    def get_comment_count(self, obj):
        return obj.comments.count()  # only runs if "comment_count" was requested
```

If a method field needs specific relations preloaded to run efficiently,
see [`requires_related`](advanced-usage.md#optimizing-serializermethodfield).

## Next steps

- [Advanced Usage](advanced-usage.md) — optimizer hints, plain `APIView`
  integration, OpenAPI docs.
- [Common Patterns](common-patterns.md) — real-world recipes.
- [Performance](performance.md) — how the query optimizer works and what
  it measurably saves.
