# Quick Start

## Enable tracing and read the header

```python
# settings.py
PERMISSION_DEBUGGER = {"ENABLED": True}
```

```python
# views.py
from drf_permission_debugger import PermissionDebugMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet


class ArticleViewSet(PermissionDebugMixin, ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwner]
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
```

A staff user's denied request:

```
GET /articles/1/
403 Forbidden

X-Permission-Trace: IsAuthenticated=granted, IsOwner=granted, IsAuthenticated=granted, IsOwner=denied
```

Each permission class appears twice here because `IsOwner` is an
*object-level* check - `IsAuthenticated`/`IsOwner` are both checked once
at the request level (`check_permissions`, before the object is even
fetched) and again at the object level (`check_object_permissions`,
once the specific `Article` is loaded) - see
[Architecture](architecture.md) for exactly when each runs.

## Get the full structured trace in the response body

```python
PERMISSION_DEBUGGER = {"ENABLED": True, "INCLUDE_IN_RESPONSE_BODY": True}
```

```json
403 Forbidden
{
  "detail": "You do not own this article.",
  "permission_trace": [
    {"permission_class": "IsAuthenticated", "granted": true, "object_level": false, "message": null, "code": null},
    {"permission_class": "IsOwner", "granted": true, "object_level": false, "message": null, "code": null},
    {"permission_class": "IsAuthenticated", "granted": true, "object_level": true, "message": null, "code": null},
    {"permission_class": "IsOwner", "granted": false, "object_level": true, "message": "You do not own this article.", "code": "not_owner"}
  ]
}
```

## Read the trace from your own code

```python
from drf_permission_debugger import get_permission_trace


class ArticleViewSet(PermissionDebugMixin, ModelViewSet):
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        trace = get_permission_trace(self)
        if trace and not trace.all_granted:
            logger.info("permission denied", extra={"trace": trace.as_dict()})
        return response
```

`get_permission_trace()` works regardless of the `PERMISSION_DEBUGGER`
setting - tracing itself always runs on a `PermissionDebugMixin` view;
`ENABLED`/`RESTRICT_TO_STAFF` only gate what's exposed over HTTP.

## Inspect a view without making a request

```python
from drf_permission_debugger import describe_view

description = describe_view(ArticleViewSet)
for permission in description["permissions"]:
    marker = " (object-level)" if permission.checks_object_permission else ""
    print(f"{permission.name}{marker}: {permission.docstring}")
```

```
IsAuthenticated: Allows access only to authenticated users.
IsOwner (object-level): Object-level only: grants everything at the request level.
```

## From the command line

```bash
python manage.py show_view_permissions /articles/1/
```

```
/articles/1/ -> myapp.views.ArticleViewSet

permission_classes (2):
  - IsAuthenticated
      Allows access only to authenticated users.
  - IsOwner [object-level]
      Object-level only: grants everything at the request level.

authentication_classes (2):
  - SessionAuthentication
  - BasicAuthentication

throttle_classes (0):
  (none)
```

See [Advanced Usage](advanced-usage.md) for combining this with
logging/monitoring, and testing the trace directly.
