# Getting Started

## Install

```bash
pip install drf-permission-debugger
```

```python
# settings.py
INSTALLED_APPS = [
    ...,
    "drf_permission_debugger",
]
```

No trace is ever attached to a response until you explicitly enable it
- see [Settings](settings.md).

## Mix into a view or viewset

```python
# views.py
from drf_permission_debugger import PermissionDebugMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet


class ArticleViewSet(PermissionDebugMixin, ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
```

`PermissionDebugMixin` must come *before* the DRF base class in the
MRO (as shown above) - it overrides `check_permissions`/
`check_object_permissions`/`finalize_response`, and needs to call
`super().finalize_response()` to get DRF's own response back before
attaching anything to it.

## Turn on the trace header

```python
# settings.py
PERMISSION_DEBUGGER = {
    "ENABLED": True,
}
```

By default, the trace is only attached for a **staff** user
(`request.user.is_staff`) - a request from anyone else gets no header
at all, even with `ENABLED: True`. Log in as staff and make a request:

```
GET /articles/1/
403 Forbidden

X-Permission-Trace: IsAuthenticated=granted, IsOwner=denied
```

See [Security](security.md) for why this restriction exists and when
it's safe to relax.

## What happens now

- A granted request still succeeds exactly as it would without this
  package - the trace header is added, but nothing about the response
  status or body changes.
- A denied request still returns the same status code (`401`/`403`)
  and the same `detail` message DRF would already produce - the trace
  is purely additional information.

See [Quick Start](quickstart.md) for the response-body trace option,
static introspection with `describe_view()`, and the
`show_view_permissions` management command.
