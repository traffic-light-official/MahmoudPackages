# Troubleshooting

## The `X-Permission-Trace` header never appears, even with `ENABLED: True`

Check, in order:

1. Is `request.user` actually authenticated and `is_staff`? This is
   the default (`RESTRICT_TO_STAFF: True`) gate - an anonymous or
   ordinary (non-staff) user never sees the header regardless of
   `ENABLED`. Log in as (or `force_authenticate` in a test as) a staff
   user, or set `RESTRICT_TO_STAFF: False` (see
   [Security](security.md) for when that's actually appropriate).
2. Does the view actually mix in `PermissionDebugMixin`? A plain
   `ModelViewSet` with no mixin produces no trace to attach at all.
3. Is `PermissionDebugMixin` listed *before* the DRF base class in the
   MRO (`class ArticleViewSet(PermissionDebugMixin, ModelViewSet)`, not
   the other way around)? If it's listed after, DRF's own
   `check_permissions`/`finalize_response` run instead of this
   package's overrides.

## `KeyError` on `response.headers["X-Permission-Trace"]` in a test

The header genuinely wasn't attached - see the checklist above. This is
also the most common test-authoring mistake: forgetting
`@override_settings(PERMISSION_DEBUGGER={"ENABLED": True})`, or
authenticating as a non-staff user with the default
`RESTRICT_TO_STAFF: True`.

## The trace shows a permission class appearing twice

Expected, not a bug - a permission class checked at both the request
level (`check_permissions`) and the object level
(`check_object_permissions`) appears once for each, since both
contribute to the same combined trace. See
[Architecture](architecture.md#why-the-trace-accumulates-across-both-request-level-and-object-level-checks).

## `"permission_trace"` never shows up in the response body

Two independent gates, both must be satisfied:

1. `INCLUDE_IN_RESPONSE_BODY: True` (default `False`).
2. The request must actually be **denied** - a granted response's body
   is never mutated, even with this setting on. See
   [Configuration](configuration.md#where-the-trace-goes).

## `show_view_permissions`/`describe_view()` says a path "does not resolve to a class-based view"

The resolved URL points at a plain function-based view (including one
wrapped with `@api_view`, which is technically class-based under the
hood but through a dynamically generated, unnamed class that isn't
useful to introspect this way) - this package's introspection tools
only work against a "real," named class-based view/viewset. Point at a
different URL, or convert the view.

## `CommandError: No URL matches '...'`

The path doesn't resolve against your project's `ROOT_URLCONF` at all -
double-check the path is exactly what a real request would use
(leading slash, trailing slash matching your `APPEND_SLASH` setting,
any URL namespace prefix).

## An undocumented custom permission class shows a description anyway

If `describe_permissions()` shows text for a permission class you
didn't document, check whether that text is genuinely that class's
*own* docstring, or - if you're seeing
`BasePermission`'s "A base class from which all permission classes
should inherit." - report it as a bug: this package deliberately
avoids falling back to an inherited docstring (see
[Architecture](architecture.md#why-describe_permissions-doesnt-fall-back-to-an-inherited-docstring)),
so seeing that specific fallback text would indicate a regression.
