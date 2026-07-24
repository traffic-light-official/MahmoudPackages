# FAQ

## Does this replace GraphQL?

Not really — it gives REST APIs the *field-selection* ergonomics people
usually reach for GraphQL to get, without adopting a schema/resolver layer,
a new query language on the wire, or GraphQL-specific tooling. If you need
client-defined queries across arbitrary relations with a single round
trip and your team is prepared to operate a GraphQL layer, that's still a
reasonable choice. If you have an existing REST API and want to cut
over-fetching without a rewrite, this is the lower-cost path.

## Does it work with `ModelViewSet`'s `create`/`update`?

Yes, output filtering and query optimization both work across every
action. By default, `fields=` is ignored on unsafe methods
(`POST`/`PUT`/`PATCH`/`DELETE`) — see
[`SAFE_METHODS_ONLY`](settings.md#safe_methods_only) — so a `POST` response
always reflects the full default representation unless you deliberately
disable that guard.

## Can clients request fields that don't exist?

By default, yes, silently — the response just won't contain a field by
that name. Set [`STRICT = True`](settings.md#strict) to turn this into an
explicit `400 Bad Request`.

## Does this expose fields that would otherwise be hidden?

No. `?fields=` can only narrow the set of fields a serializer would have
exposed anyway. It has no ability to add fields that aren't declared on the
serializer, and any permission-based field hiding you implement in
`get_fields()` (see [Common Patterns](common-patterns.md#feature-flagged-fields))
still applies — this package's filtering runs on top of, not instead of,
your own field logic.

## Why do I need the mixin on nested serializers too?

Each serializer instance is responsible for filtering its *own* level of
the response tree — there's no global registry rewriting fields across
every serializer in a project. If a nested serializer doesn't use
`PartialFieldsSerializerMixin`, it renders its full default representation
regardless of what the client requested for it. This is a deliberate
design choice: it keeps the mixin's behavior local and predictable rather
than depending on implicit, action-at-a-distance configuration.

## Does the optimizer ever get it wrong and break my API?

No — see [Architecture](architecture.md#design-principles): the optimizer
is deliberately conservative and only ever *adds* `select_related` /
`prefetch_related` / `only()`, never changes what data is returned. If it
can't confidently map a field to a model relation or column, it leaves
that field alone (falls back to normal, unoptimized attribute access) —
see [Troubleshooting](troubleshooting.md) for the specific cases.

## Can I use this with `django-filter`, `django-guardian`, multi-tenancy packages, etc.?

Yes — this package only touches `get_queryset()` (adding
`select_related`/`prefetch_related`/`only()`) and `get_fields()` on the
serializer. It composes with any other `get_queryset()` override or
serializer field logic already in your MRO. See
[Advanced Usage](advanced-usage.md#combining-with-django-filter-custom-get_queryset).

## Does this support GraphQL-style field aliasing collisions?

If a client aliases two different fields to the same output key
(`?fields=a:x,a:y`), that's rejected at parse time as a duplicate field
name within the same group (`a` would be requested twice) — see
[Troubleshooting](troubleshooting.md#invalidfieldsparametererror-field-was-requested-more-than-once).

## Is this thread-safe / safe for async views?

Yes. There is no shared mutable state between requests — `FieldTree` is an
immutable, frozen dataclass, and `PartialResponseMixin` caches the parsed
tree per view *instance*, and DRF creates a new view instance per request
(both sync and async).

## Why isn't there a management command or Django admin integration?

The scope of this package is deliberately narrow: serializer field
filtering and queryset optimization for the DRF request/response cycle.
Django admin uses its own `ModelAdmin`/form machinery, which this package
doesn't touch.
