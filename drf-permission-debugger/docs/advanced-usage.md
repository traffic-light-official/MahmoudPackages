# Advanced Usage

## Logging every denial with structured context

```python
import logging

from drf_permission_debugger import PermissionDebugMixin, get_permission_trace

logger = logging.getLogger("myapp.permissions")


class AuditedPermissionsMixin(PermissionDebugMixin):
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        trace = get_permission_trace(self)
        if trace and not trace.all_granted:
            denied = trace.denied_by
            logger.warning(
                "permission_denied",
                extra={
                    "path": request.path,
                    "user": getattr(request.user, "pk", None),
                    "denied_by": denied.permission_class if denied else None,
                    "trace": trace.as_dict(),
                },
            )
        return response
```

This works independently of the `PERMISSION_DEBUGGER` setting - tracing
always runs on any view mixing in `PermissionDebugMixin`; `ENABLED`
only controls whether the trace is exposed over HTTP, not whether it
exists for your own code to read.

## Combining with a custom `finalize_response`

If your viewset already overrides `finalize_response` for something
else (a custom header, a deprecation notice), call `super()` in the
normal MRO order - `PermissionDebugMixin` only adds its own header/body
mutation on top of whatever `super().finalize_response()` returns, it
doesn't replace it:

```python
class ArticleViewSet(PermissionDebugMixin, DeprecationHeaderMixin, ModelViewSet):
    ...
```

## Testing the trace directly, without a real HTTP response

```python
from drf_permission_debugger import get_permission_trace
from rest_framework.test import APIRequestFactory


def test_trace_records_both_permissions(db):
    request = APIRequestFactory().get("/articles/1/")
    view = ArticleViewSet()
    view.request = view.initialize_request(request)
    view.check_permissions(view.request)

    trace = get_permission_trace(view)
    assert [r.permission_class for r in trace.results] == ["IsAuthenticated", "IsOwner"]
```

Useful for unit-testing the trace itself without going through a full
`dispatch()` cycle - see [Testing](testing.md) for the more common
end-to-end approach (asserting the response header/body directly).

## Using `describe_permissions()` in your own test suite

Assert a view is guarded by the permission class you expect, without
making any request at all:

```python
from drf_permission_debugger import describe_permissions


def test_article_viewset_requires_ownership():
    names = [p.name for p in describe_permissions(ArticleViewSet)]
    assert "IsOwner" in names
```

This catches an accidentally-removed permission class at test time,
the same way a "this endpoint requires auth" smoke test would, but
without needing a real request/response round trip.

## Restricting the trace to a specific subset of staff

`RESTRICT_TO_STAFF` is an all-or-nothing gate on `is_staff` - if you
need finer control (e.g. only a specific permission group), override
`finalize_response` yourself instead of relying on the built-in gate:

```python
class ArticleViewSet(PermissionDebugMixin, ModelViewSet):
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        trace = get_permission_trace(self)
        if trace and request.user.groups.filter(name="debuggers").exists():
            response["X-Permission-Trace"] = trace.as_header_value()
        return response
```

Set `PERMISSION_DEBUGGER = {"ENABLED": False}` project-wide first, so
the built-in mechanism never also attaches the header - this pattern
replaces it entirely rather than layering on top of it.
