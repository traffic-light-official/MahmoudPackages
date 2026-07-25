# Examples

A complete, runnable example lives in [`examples/blog/`](https://github.com/MahmoudGShake/MahmoudPackages/tree/master/drf-permission-debugger/examples/blog)
in the source repository - models, a custom object-level permission, a
viewset, and a script exercising a granted request, a denied request,
and static introspection, with no test framework and no running server.

Run it yourself:

```bash
git clone https://github.com/MahmoudGShake/MahmoudPackages.git
cd MahmoudPackages/drf-permission-debugger
pip install -e ".[dev]"
python -m examples.blog.example
```

## `examples/blog/permissions.py`

```python
from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """Object-level only: grants everything at the request level."""

    message = "You do not own this article."
    code = "not_owner"

    def has_object_permission(self, request, view, obj):
        user = request.user
        return bool(user and user.is_authenticated and obj.owner_id == user.id)
```

## `examples/blog/views.py`

```python
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from drf_permission_debugger import PermissionDebugMixin
from examples.blog.models import Article
from examples.blog.permissions import IsOwner
from examples.blog.serializers import ArticleSerializer


class ArticleViewSet(PermissionDebugMixin, ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = ArticleSerializer
    queryset = Article.objects.select_related("owner").all()
```

## `examples/blog/example.py` output

```text
== Owner retrieves their own article: granted, no trace (debugger disabled) ==
  GET /articles/1/ -> 200
  X-Permission-Trace present: False

== Same request, debugger enabled: granted, trace still attached ==
  GET /articles/1/ -> 200
  X-Permission-Trace: IsAuthenticated=granted, IsOwner=granted, IsAuthenticated=granted, IsOwner=granted

== A different staff user retrieves it: denied, full trace ==
  GET /articles/1/ -> 403
  X-Permission-Trace: IsAuthenticated=granted, IsOwner=granted, IsAuthenticated=granted, IsOwner=denied
  Body: {'detail': 'You do not own this article.', 'permission_trace': [{'permission_class': 'IsAuthenticated', 'granted': True, 'object_level': False, 'message': None, 'code': None}, {'permission_class': 'IsOwner', 'granted': True, 'object_level': False, 'message': None, 'code': None}, {'permission_class': 'IsAuthenticated', 'granted': True, 'object_level': True, 'message': None, 'code': None}, {'permission_class': 'IsOwner', 'granted': False, 'object_level': True, 'message': 'You do not own this article.', 'code': 'not_owner'}]}

== Static introspection, no request at all ==
  IsAuthenticated: Allows access only to authenticated users.
  IsOwner (object-level): Object-level only: grants everything at the request level.
```

A few things worth noting from this output:

- The first request (debugger disabled) is identical in every way to
  what a plain `ModelViewSet` without `PermissionDebugMixin` would
  produce - `200`, no extra header - proving the mixin is inert until
  explicitly enabled.
- `IsAuthenticated`/`IsOwner` each appear **twice** in the trace: once
  from `check_permissions()` (request-level, before the object is
  fetched) and once from `check_object_permissions()` (object-level,
  once the specific `Article` is loaded) - see
  [Architecture](architecture.md#why-the-trace-accumulates-across-both-request-level-and-object-level-checks).
- The static introspection section at the bottom made zero HTTP
  requests - `describe_view()` reads `ArticleViewSet.permission_classes`
  directly.

See [Quick Start](quickstart.md) for the same scenarios explained step
by step.
