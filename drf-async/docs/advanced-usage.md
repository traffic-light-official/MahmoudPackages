# Advanced Usage

## Custom `@action`-decorated routes on an async viewset

`@rest_framework.decorators.action` works unchanged on
[`AsyncModelViewSet`](api-reference.md#asyncmodelviewset)/
[`AsyncGenericViewSet`](api-reference.md#asyncgenericviewset) - define
the extra action as `async def`, exactly like the built-in CRUD
actions:

```python
from rest_framework.decorators import action
from rest_framework.response import Response

from drf_async import AsyncModelViewSet


class ArticleViewSet(AsyncModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

    @action(detail=True, methods=["post"])
    async def publish(self, request, *args, **kwargs):
        article = await self.aget_object()
        article.published = True
        await article.asave()
        return Response(self.get_serializer(article).data)
```

`AsyncGenericViewSet.as_view()` inspects every bound action (including
extra `@action`-decorated ones) and marks the returned view callable as
async only if *all* of them are coroutine functions - see
[Architecture](architecture.md#why-as_view-needs-an-override) for why
this check exists at all. Mixing a sync `@action` method into an
otherwise-async viewset works too, but the whole view is then treated
as synchronous by Django, so every action on it (including the async
ones) runs through Django's sync-view machinery instead - keep a
viewset's actions all-sync or all-async.

## Writing a genuinely async `create`/`update`/`destroy`

The default `aperform_create`/`aperform_update`/`aperform_destroy`
bridge `serializer.save()`/`instance.adelete()` in the way that matches
DRF's own synchronous mixins exactly (`aperform_destroy` already uses
`instance.adelete()` directly). Override `aperform_create`/
`aperform_update` when you want to skip the serializer's own `.save()`
entirely and use the async ORM yourself - useful when creation involves
more than a single model's fields:

```python
from drf_async import AsyncCreateModelMixin, AsyncGenericAPIView


class ArticleCreateView(AsyncCreateModelMixin, AsyncGenericAPIView):
    serializer_class = ArticleSerializer
    queryset = Article.objects.all()

    async def aperform_create(self, serializer):
        article = await Article.objects.acreate(**serializer.validated_data)
        await AuditLog.objects.acreate(action="article_created", target_id=article.pk)
```

`serializer.is_valid(raise_exception=True)` still runs first (bridged
through a thread, since validators may query the database) - only the
save step itself changes.

## Combining async and sync permission/throttle classes

```python
class ArticleViewSet(AsyncModelViewSet):
    permission_classes = [IsAuthenticated, HasValidApiKey]  # sync, then async
    throttle_classes = [UserRateThrottle, BurstRateThrottle]  # sync, then async
```

`acheck_permissions()`/`acheck_throttles()` iterate the list in order,
awaiting each check regardless of whether the underlying class is
sync (bridged) or async (awaited directly) - the two kinds compose with
no special ordering requirement.

## Object-level permissions

`AsyncGenericAPIView.aget_object()` calls
`self.acheck_object_permissions(self.request, obj)` after fetching the
object, mirroring `GenericAPIView.get_object()`'s own
`check_object_permissions()` call - a `BaseAsyncPermission` subclass's
`has_object_permission` (or a sync `BasePermission`'s) is checked the
same way `has_permission` is, bridged or awaited as appropriate.

```python
class IsOwner(BaseAsyncPermission):
    async def has_object_permission(self, request, view, obj):
        return obj.author_id == request.user.id
```

## Calling a sync-only third-party permission/throttle from an async view

Nothing needs to change - `call_maybe_async()` detects any callable
that isn't a native coroutine function and bridges it through
`sync_to_async(..., thread_sensitive=True)` automatically, so a
third-party `BasePermission`/`BaseThrottle` subclass you don't control
works exactly as it would on a plain sync `APIView`.

## Testing views without a real ASGI server

See [Testing](testing.md) for using `django.test.AsyncClient`/
`AsyncRequestFactory` directly against `AsyncAPIView`/
`AsyncGenericAPIView` subclasses, including the pytest-django
transaction-isolation caveat that async ORM tests need to know about.
