# Configuration

Most projects need no configuration at all — every setting has a sane
default. This page covers the decisions worth making deliberately before
you roll this out broadly. For the exhaustive list of settings and their
defaults, see [Settings](settings.md).

## Choosing where to apply the mixins

- **Serializers**: apply `PartialFieldsSerializerMixin` (or use
  `PartialFieldsModelSerializer`/`PartialFieldsSerializer`) on every
  serializer that should support `?fields=`, *including nested serializers*.
  A nested serializer that doesn't use the mixin will always render its
  full default representation, ignoring any nested selection the client
  requested for it.
- **Views**: apply `PartialResponseMixin` on every `GenericAPIView` /
  viewset that should expose `?fields=` and get automatic query
  optimization. For plain `APIView` subclasses, see
  [Advanced Usage](advanced-usage.md#plain-apiview-integration).

## Deciding on `STRICT` mode

By default (`STRICT = False`), requesting an unknown field name is a
silent no-op — the response simply won't contain a field by that name.
This matches the permissive behavior most sparse-fieldset implementations
use, and avoids leaking information about field names that exist on the
serializer but were deliberately hidden by a permission check elsewhere.

Enable `STRICT = True` if you'd rather clients get an explicit `400` when
they typo a field name — useful for internal APIs where you control every
client and want fast feedback during development. See
[`docs/settings.md#strict`](settings.md#strict).

## Deciding on `SAFE_METHODS_ONLY`

This is enabled by default and you should almost never disable it. DRF
serializers use the *same* field set for input validation (`POST`/`PUT`/
`PATCH`) and output rendering. Without this guard, a client could send
`?fields=title` on a `POST` and make every other writable field vanish from
input validation — silently bypassing required-field checks. With the
default enabled, `?fields=` is only honored on safe methods (`GET`, `HEAD`,
`OPTIONS`); unsafe methods always see the full field set. See
[`docs/security.md`](security.md) for the full reasoning.

## Deciding on query optimization

`ENABLE_QUERY_OPTIMIZATION` defaults to `True`. Turn it off only if you've
identified a specific queryset where the automatic `select_related` /
`prefetch_related` / `only()` inference does the wrong thing (see
[Troubleshooting](troubleshooting.md) for the known cases where it
deliberately does nothing) and you'd rather optimize that view manually
without the mixin fighting your `get_queryset()` override.

## Setting up OpenAPI documentation

If you use drf-spectacular, decide between:

- Adding `fields_query_parameter()` to `@extend_schema(parameters=[...])`
  on individual views, or
- Setting `schema = PartialResponseAutoSchema()` on every view that uses
  `PartialResponseMixin`, to document the parameter automatically.

See [Advanced Usage](advanced-usage.md#openapi-documentation).

## Example project-wide configuration

```python
# settings.py
PARTIAL_RESPONSE_FIELDS = {
    "QUERY_PARAM": "fields",
    "STRICT": False,
    "MAX_DEPTH": 4,
    "ALWAYS_INCLUDE": ["id", "url"],
}
```
