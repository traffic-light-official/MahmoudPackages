# Common Patterns

## Mobile clients requesting a minimal payload

```
GET /articles/?fields=id,title,thumbnail_url
```

Pair this with `ALWAYS_INCLUDE` to guarantee clients always get whatever
identifier your mobile app's local cache keys on, even if they forget to
ask for it:

```python
PARTIAL_RESPONSE_FIELDS = {"ALWAYS_INCLUDE": ["id", "updated_at"]}
```

## BFF (Backend-for-Frontend) aggregation layers

A BFF that stitches together several backend calls often only needs a few
fields from each. Rather than maintaining a slim serializer per BFF
consumer, let each consumer ask for what it needs from one full-featured
serializer:

```
GET /internal/articles/?fields=id,title,author(id)
```

## GraphQL-style nested resolution without GraphQL

If you want field-selection ergonomics but don't want to adopt a GraphQL
schema and resolver layer, this package gets you most of the way there for
read-heavy REST endpoints, with far less operational surface area.

## Feature-flagged fields

Combine with a custom `get_fields()` override *after* this mixin (later in
`to_representation`, or by overriding `get_queryset`) to hide fields behind
a feature flag, independent of what the client requested:

```python
class ArticleSerializer(PartialFieldsModelSerializer):
    class Meta:
        model = Article
        fields = ["id", "title", "beta_summary"]

    def get_fields(self):
        fields = super().get_fields()
        if not self.context["request"].user.has_perm("articles.beta_features"):
            fields.pop("beta_summary", None)
        return fields
```

Because `PartialFieldsSerializerMixin.get_fields()` already filtered by the
`fields` parameter, this runs on the *already-narrowed* field set — a
client cannot request `beta_summary` back into existence by asking for it
explicitly if the permission check removes it here.

## Versioned field renaming during a migration

When renaming a model field, use aliasing to support both the old and new
public names during a deprecation window without duplicating serializers:

```python
class ArticleSerializer(PartialFieldsModelSerializer):
    class Meta:
        model = Article
        fields = ["id", "headline"]  # renamed from `title`
```

```
# Old clients, unaware of the rename:
GET /articles/?fields=title:headline

# New clients:
GET /articles/?fields=headline
```

## Read-heavy dashboards with aggregates

See [`docs/examples.md#a-dashboard-endpoint-requesting-only-aggregate-fields`](examples.md#a-dashboard-endpoint-requesting-only-aggregate-fields)
for combining `annotate()` with sparse fieldsets — annotated values are
recognized by the optimizer and never mistaken for relations.

## Defense against overly broad requests

For public-facing APIs, cap nesting depth and payload size so a client
can't force pathological amounts of work:

```python
PARTIAL_RESPONSE_FIELDS = {"MAX_DEPTH": 3, "MAX_FIELDS_LENGTH": 300}
```

See [Security](security.md) for the full threat model.
