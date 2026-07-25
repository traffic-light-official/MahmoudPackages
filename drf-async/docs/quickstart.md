# Quick Start

## A full async CRUD viewset

```python
# models.py
class Article(models.Model):
    title = models.CharField(max_length=200, unique=True)
    author = models.ForeignKey("auth.User", on_delete=models.CASCADE)
```

```python
# serializers.py
from rest_framework import serializers


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ["id", "title", "author"]
```

```python
# views.py
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from drf_async import AsyncModelViewSet


class ArticleViewSet(AsyncModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
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

Every request is handled by a real coroutine end to end: permission
and pagination checks bridge through a thread automatically (they're
plain sync DRF classes here), while `list`/`retrieve`/`create`/
`update`/`destroy` themselves use the async ORM directly - `async for
obj in queryset`, `queryset.aget(...)`, `instance.adelete()`.

## Writing an async-native permission

```python
# permissions.py
import httpx
from drf_async import BaseAsyncPermission


class HasValidApiKey(BaseAsyncPermission):
    message = "Missing or invalid API key."

    async def has_permission(self, request, view):
        api_key = request.headers.get("X-Api-Key")
        if not api_key:
            return False
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://auth.example.com/validate", headers={"X-Api-Key": api_key}
            )
        return response.status_code == 200
```

```python
class ArticleViewSet(AsyncModelViewSet):
    permission_classes = [HasValidApiKey]
    ...
```

Checking an external service over the network like this would block
the event loop for the entire round trip if it had to run through a
plain sync `BasePermission` (bridged via a thread, which works, but
still ties up a worker thread for the whole call) - a genuinely async
permission awaits the network call directly instead.

## Writing an async-native throttle

```python
# throttles.py
from drf_async import AsyncSimpleRateThrottle


class BurstRateThrottle(AsyncSimpleRateThrottle):
    scope = "burst"

    def get_cache_key(self, request, view):
        ident = request.user.pk if request.user.is_authenticated else self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}
```

```python
# settings.py
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_RATES": {"burst": "30/min"},
}
```

```python
class ArticleViewSet(AsyncModelViewSet):
    throttle_classes = [BurstRateThrottle]
    ...
```

Reads/writes the sliding window through Django's async cache API
(`cache.aget`/`.aset`) directly - no thread hop, since a cache
round trip has no serialization or database work behind it.

## Writing a genuinely async `create`/`update`

The default `aperform_create`/`aperform_update` bridge
`serializer.save()` through a thread (since it may run
database-touching validators and call the model's own `save()`).
Override them to use the async ORM directly instead:

```python
class ArticleViewSet(AsyncModelViewSet):
    async def aperform_create(self, serializer):
        await Article.objects.acreate(**serializer.validated_data)
```

See [Advanced Usage](advanced-usage.md) for when this is worth doing.

## A single async view with no model behind it

```python
from drf_async import AsyncAPIView
from rest_framework.response import Response


class HealthCheckView(AsyncAPIView):
    async def get(self, request, *args, **kwargs):
        db_ok = await check_database()
        cache_ok = await check_cache()
        return Response({"database": db_ok, "cache": cache_ok})
```
