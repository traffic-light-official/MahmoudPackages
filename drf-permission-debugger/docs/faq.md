# FAQ

## Does this package change who is authorized to do what?

No - never. See
[Architecture](architecture.md#the-core-guarantee-identical-behavior-to-a-plain-apiview)
for exactly how `check_permissions`/`check_object_permissions` are kept
behaviorally identical to DRF's own `APIView`, and
`tests/test_integration.py::TestBehaviorIsUnchanged` for the tests
proving it.

## Why is the trace header missing even though I set `ENABLED: True`?

Almost always `RESTRICT_TO_STAFF` (default `True`) - the requesting
user must be authenticated and `is_staff`. See
[Troubleshooting](troubleshooting.md).

## Can I see the trace for a granted (successful) request, not just a denial?

Yes - the header is attached to *every* response (granted or denied)
once debugging is authorized; only the response-*body* addition
(`INCLUDE_IN_RESPONSE_BODY`) is denial-only, since there's no
interesting "why" to explain for a successful, expected outcome. See
[Configuration](configuration.md#where-the-trace-goes).

## Does this work with function-based views (`@api_view`)?

`PermissionDebugMixin` mixes into class-based views/viewsets only - a
function decorated with `@api_view` is wrapped in a dynamically
generated `APIView` subclass by DRF itself, and there's no clean way to
inject a mixin into that. Convert the view to a class-based one, or
wrap it manually. `show_view_permissions`/`describe_view()` also only
work against class-based views for the same reason - see
[Troubleshooting](troubleshooting.md).

## Does `describe_permissions()` need a live request or database?

No - it only reads `view_class.permission_classes`, a plain class
attribute, and each class's own docstring. No instantiation, no
database, no `@pytest.mark.django_db` required.

## Can I customize the trace's format (e.g. JSON instead of the compact header string)?

The header is always the compact `as_header_value()` summary - if you
need a different format, read the trace yourself via
`get_permission_trace()` in your own `finalize_response` override and
format it however you like (see
[Advanced Usage](advanced-usage.md#restricting-the-trace-to-a-specific-subset-of-staff)
for the general pattern), rather than relying on the built-in header
attachment.

## Does this package work with object-level permissions that are never actually checked (a view that never calls `get_object()`)?

Yes, transparently - `check_object_permissions` only runs (and only
then contributes to the trace) when the view itself calls
`self.check_object_permissions(...)` (typically inside
`get_object()`). A `list`/`create` action that never fetches a specific
object simply never has an object-level entry in its trace - there's
nothing to record.

## Is there a way to see the trace in the Django admin or a debug toolbar panel?

Not built in - this package focuses on the HTTP response itself
(header/body) and programmatic access (`get_permission_trace()`). A
`django-debug-toolbar` panel or admin integration would be a reasonable
addition built *on top of* `get_permission_trace()`; open an issue if
you'd like to contribute one (see [Contributing](contributing.md)).
