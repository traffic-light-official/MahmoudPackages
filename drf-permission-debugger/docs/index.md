# drf-permission-debugger

Understand exactly why a Django REST Framework permission check
granted or denied a request - without changing its behavior.

```python
from drf_permission_debugger import PermissionDebugMixin


class ArticleViewSet(PermissionDebugMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
```

```
X-Permission-Trace: IsAuthenticated=granted, IsOwnerOrReadOnly=denied
```

## Why this exists

A `403 Forbidden` from DRF tells you a request was denied - not
*which* of your (possibly several) configured permission classes
denied it, or why, once `permission_classes` has more than one entry.
Reproducing the decision by reading code and guessing which class fired
gets tedious fast, especially with object-level checks that only run
after a request-level check already passed. This package records every
configured permission class's outcome, in the exact order and with the
exact early-exit-on-first-denial behavior DRF's own
`check_permissions()`/`check_object_permissions()` already have -
mixing it in never changes who is authorized to do what, only what you
can *see* about that decision, and only when you've explicitly opted in.

## Where to go next

- New to the package? Start with [Getting Started](getting-started.md).
- Want the exact guarantee about behavior never changing? Read
  [Architecture](architecture.md).
- Looking for a specific class or function? Jump to
  [API Reference](api-reference.md).
- Something not behaving as expected? Check
  [Troubleshooting](troubleshooting.md) and the [FAQ](faq.md).

## At a glance

| Task | Where |
| --- | --- |
| Record why a request was granted/denied | [`PermissionDebugMixin`](api-reference.md#permissiondebugmixin) |
| Turn on the trace header | [`PERMISSION_DEBUGGER`](settings.md) setting (`ENABLED`) |
| Include the trace in a denied response body | [`INCLUDE_IN_RESPONSE_BODY`](settings.md) setting |
| Inspect a view's permission stack with no live request | [`describe_view()`](api-reference.md#describe_view) |
| Inspect from the command line | `python manage.py show_view_permissions <path>` |
