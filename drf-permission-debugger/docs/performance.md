# Performance

## Tracing always runs, but is nearly free

`PermissionDebugMixin.check_permissions`/`check_object_permissions`
call the exact same `permission.has_permission()`/
`has_object_permission()` DRF's own `APIView` already calls - the only
addition per check is constructing one small `PermissionCheckResult`
dataclass and appending it to a list. There is no I/O, no
serialization, and no database access anywhere in the recording path
itself - the cost is a handful of attribute lookups and one list
append per configured permission class, on every request, regardless
of whether `ENABLED` is `True`.

## `finalize_response`'s work only happens when debugging is authorized

`_is_debugging_authorized(request)` (an `ENABLED` check, then - unless
`RESTRICT_TO_STAFF` is `False` - an `is_authenticated`/`is_staff` check
on `request.user`) short-circuits before anything else in
`finalize_response` runs. For the overwhelming majority of requests in
a production deployment (`ENABLED: False`, the default, or a non-staff
user even with it on), the header/body attachment code never executes
at all - just one settings lookup and an early return.

## `INCLUDE_IN_RESPONSE_BODY` only mutates a denied response's body

The `response.data["permission_trace"] = ...` assignment only runs
when `not trace.all_granted` - a granted (successful) response's body
is never touched, so there's no serialization cost added to your
endpoint's normal, successful hot path even when this setting is on.

## Static introspection (`describe_permissions`/`describe_view`) does no request-time work at all

These functions only read `view_class.permission_classes` (a plain
class attribute) and call `inspect.cleandoc()` on each class's own
`__doc__` - there's no instantiation, no `has_permission()` call, and
no request object involved. Safe to call at import time, in a
management command, or in a test's collection phase without any
per-request overhead consideration.

## Recommended: don't wrap `get_permission_trace()` calls in a loop

`get_permission_trace(view)` is a single `getattr()` - cache the result
in a local variable if you need it more than once within the same
`finalize_response()` call, the same way you'd avoid redundant
attribute lookups anywhere else; the trace itself doesn't change after
`check_permissions`/`check_object_permissions` have finished running.
