# Common Patterns

## Migrating an existing sync viewset incrementally

Convert one action at a time by keeping the sync base class for
actions you haven't converted yet, and overriding just the ones you
have - as long as *every bound action on a given `as_view()` call* ends
up async or ends up sync, not a mix (see
[Architecture](architecture.md#why-as_view-needs-an-override)):

```python
# Step 1: convert read-only actions first (the common hot path)
from drf_async import AsyncListModelMixin, AsyncRetrieveModelMixin
from drf_async.generics import AsyncGenericAPIView
from rest_framework.viewsets import GenericViewSet


class ArticleViewSet(AsyncListModelMixin, AsyncRetrieveModelMixin, AsyncGenericAPIView, GenericViewSet):
    ...
```

In practice this is easiest to reason about one whole viewset at a
time rather than one action at a time within the same viewset - convert
`ArticleViewSet` fully, move to the next model, rather than leaving one
viewset half-async.

## A health check view with no model behind it

```python
from drf_async import AsyncAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


class HealthCheckView(AsyncAPIView):
    permission_classes = [AllowAny]

    async def get(self, request, *args, **kwargs):
        checks = {
            "database": await self._check_database(),
            "cache": await self._check_cache(),
        }
        status_code = 200 if all(checks.values()) else 503
        return Response(checks, status=status_code)

    async def _check_database(self) -> bool:
        try:
            await Article.objects.aexists()
            return True
        except Exception:
            return False

    async def _check_cache(self) -> bool:
        from django.core.cache import cache

        await cache.aset("healthcheck", "1", timeout=5)
        return await cache.aget("healthcheck") == "1"
```

Both checks run concurrently-friendly (no thread hop for either one) -
awaiting them sequentially here is fine since each is fast, but nothing
stops using `asyncio.gather()` if a health check grows to include a
slow external dependency.

## Calling an external API from inside a view without blocking the loop

```python
import httpx
from drf_async import AsyncAPIView
from rest_framework.response import Response


class WeatherView(AsyncAPIView):
    async def get(self, request, *args, **kwargs):
        city = request.query_params["city"]
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://weather.example.com/{city}")
        return Response(response.json())
```

Use an async HTTP client (`httpx.AsyncClient`, `aiohttp`) here, not
`requests` - a sync client would block the event loop for the entire
round trip, and bridging it through `sync_to_async` just moves the
block to a worker thread instead of eliminating it. This is the same
category of check-a-remote-service problem
[`BaseAsyncPermission`](quickstart.md#writing-an-async-native-permission)
solves for permission checks.

## Combining an async viewset with DRF's schema generation

`drf-spectacular`/DRF's own `AutoSchema` introspect a viewset's action
methods (`list`, `create`, ...) by name and signature, not by whether
they're coroutines - schema generation works unchanged against
`AsyncModelViewSet` with no extra configuration, since the router
integration and action naming are identical to a sync `ModelViewSet`.

## Writing a mixed REST + WebSocket-adjacent app

This package only addresses DRF's request/response views - it has
nothing to do with Django Channels or WebSocket consumers. A project
using both typically has `AsyncModelViewSet`-based REST endpoints
alongside separate Channels `AsyncConsumer` classes, sharing the same
async ORM calls and the same ASGI application entry point, but with no
direct integration between the two - see [FAQ](faq.md#does-this-package-work-with-django-channels).

## Testing an async view's permission denial message

```python
async def test_denied_permission_message(api_client):
    response = await api_client.get("/guarded/")
    assert response.status_code == 403
    assert response.json()["detail"] == "Unknown client."
```

Set `authentication_classes = []` on the view under test if you expect
your own permission's `message` in the body rather than DRF's generic
`"Authentication credentials were not provided."` - see
[Troubleshooting](troubleshooting.md#my-permissions-message-is-being-replaced-with-a-generic-one).
