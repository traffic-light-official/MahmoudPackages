# Getting Started

## Install

```bash
pip install drf-async
```

```python
# settings.py
INSTALLED_APPS = [
    ...,
    "drf_async",
]
```

No further settings are required - see [Settings](settings.md) for the
handful of existing DRF settings this package's classes read from.

## Write a single async view

```python
# views.py
from drf_async import AsyncAPIView
from rest_framework.response import Response


class PingView(AsyncAPIView):
    async def get(self, request, *args, **kwargs):
        return Response({"pong": True})
```

Register it exactly like any other class-based view:

```python
# urls.py
from django.urls import path
from .views import PingView

urlpatterns = [
    path("ping/", PingView.as_view()),
]
```

## Write an async CRUD viewset

```python
# views.py
from drf_async import AsyncModelViewSet


class ArticleViewSet(AsyncModelViewSet):
    queryset = Article.objects.select_related("author").all()
    serializer_class = ArticleSerializer
```

```python
# urls.py
from rest_framework.routers import DefaultRouter
from .views import ArticleViewSet

router = DefaultRouter()
router.register("articles", ArticleViewSet)
urlpatterns = router.urls
```

`DefaultRouter`/`SimpleRouter` need no special handling here -
`AsyncModelViewSet`'s action methods are named `list`/`create`/
`retrieve`/`update`/`partial_update`/`destroy`, identically to DRF's own
sync `ModelViewSet`, just defined as `async def`.

## Serve it over ASGI

```bash
uvicorn myproject.asgi:application
```

`AsyncAPIView` still works under a WSGI server (`runserver`, `gunicorn`
with a sync worker) - Django transparently wraps each async view in its
own event loop per request in that case - but you only get real
concurrency benefit from async views when the server itself is ASGI,
so that many requests can share one event loop. See
[Deployment](deployment.md).

## What happens now

- A `GET /articles/` request lists articles using the async ORM
  underneath (`async for obj in queryset`), never blocking the event
  loop on a database round trip.
- `permission_classes`/`authentication_classes`/`throttle_classes` work
  exactly as they do on a sync view - existing sync classes are bridged
  automatically through a thread; see [Advanced Usage](advanced-usage.md)
  for writing a genuinely async permission or throttle instead.

See [Quick Start](quickstart.md) for a complete walkthrough including
async permissions, async throttles, and pagination.
