# Configuration

Every setting has a sane default; most projects need none of this. This
page covers the decisions worth making deliberately. See
[Settings](settings.md) for the exhaustive reference.

## Deciding on tool names

By default, a tool's name is `f"{base_name}{NAME_SEPARATOR}{action}"`,
where `base_name` is a snake_case version of the viewset class name with
any trailing `ViewSet`/`APIView`/`View` suffix stripped. Override with
`name_prefix=` on `@expose_as_tool` when the default would collide or
read poorly (e.g. multiple viewsets over the same model).

## Deciding what to expose

Only list the actions you actually want an LLM to be able to call:

```python
@expose_as_tool(actions=["list", "retrieve"])  # read-only
class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
    ...
```

There is no implicit "expose everything" mode — every action must be
named explicitly, so a code reviewer can see exactly what surface area an
agent gets from reading the decorator call.

## Deciding on `ENFORCE_PERMISSIONS`

Leave this enabled (the default). `execute_tool()` dispatches through the
viewset's real `.as_view()`, which means DRF's `permission_classes` are
checked exactly as they would be for a genuine HTTP request. Disabling
this is only appropriate for a fully trusted internal execution context
that performs its own authorization before calling `execute_tool()`.

## Deciding on permission modeling for agent identities

`execute_tool(name, arguments, user=...)` dispatches *as* whatever Django
user you pass. Common patterns:

- **Per-end-user agents**: pass the actual `request.user` the agent is
  acting on behalf of, so permission classes like `IsAuthenticated` or
  object-level permissions apply exactly as they would for that user
  browsing your site directly.
- **A dedicated service account**: create a Django user (e.g.
  `User.objects.get(username="llm-agent")`) with a deliberately scoped
  permission set, and pass that.
- **Fully anonymous**: omit `user` — dispatches as
  `AnonymousUser`, appropriate only for `permission_classes = []` (public)
  viewsets.

See [Security](security.md) for the full reasoning.

## Enum sizes and schema depth

`MAX_ENUM_VALUES` and `MAX_SCHEMA_DEPTH` bound worst-case generated schema
size — tune them down for public-facing agent integrations where an
oversized generated schema would waste context window, and up only if you
have legitimately large choice sets or deep object graphs.

## Example project-wide configuration

```python
# settings.py
LLM_GATEWAY = {
    "NAME_SEPARATOR": "_",
    "MAX_ENUM_VALUES": 50,
    "MAX_SCHEMA_DEPTH": 4,
    "ENFORCE_PERMISSIONS": True,
}
```
