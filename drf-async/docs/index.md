# drf-async

Modern async support for Django REST Framework: an async-native
`APIView`/`GenericAPIView`/`ModelViewSet`, with correct sync/async
bridging for authentication, permissions, throttling, and pagination -
so your handler code can use Django's real async ORM directly.

```python
from drf_async import AsyncModelViewSet


class ArticleViewSet(AsyncModelViewSet):
    queryset = Article.objects.select_related("author").all()
    serializer_class = ArticleSerializer
```

## Why this exists

DRF's `APIView.dispatch()` calls the resolved handler method
synchronously: `response = handler(request, *args, **kwargs)`. Define
`async def get(self, request)` on a plain `APIView` and this assigns an
unawaited coroutine as the "response," which breaks immediately -
DRF's own view classes predate Django's async view support entirely
and were never updated to opt into it. This package provides a
`dispatch()` that is a real coroutine throughout, correctly bridging
DRF's synchronous permission/throttle/serializer internals (which may
touch the database) through a thread via `sync_to_async`, while your
own handler code and queryset access use Django's real async ORM
(`aget`, `acreate`, `aiterator`, `async for`) directly, with no thread
hop at all.

## Where to go next

- New to the package? Start with [Getting Started](getting-started.md).
- Want to know exactly which parts of a request are bridged through a
  thread and why? Read [Architecture](architecture.md).
- Looking for a specific class or function? Jump to
  [API Reference](api-reference.md).
- Something not behaving as expected? Check
  [Troubleshooting](troubleshooting.md) and the [FAQ](faq.md).

## At a glance

| Task | Where |
| --- | --- |
| A single async view | [`AsyncAPIView`](api-reference.md#asyncapiview) |
| Async list/create/retrieve/update/destroy views | [`AsyncGenericAPIView`](api-reference.md#asyncgenericapiview) + 9 concrete views |
| Async CRUD viewset for a router | [`AsyncModelViewSet`](api-reference.md#asyncmodelviewset) / [`AsyncReadOnlyModelViewSet`](api-reference.md#asyncreadonlymodelviewset) |
| Write a permission check as a coroutine | [`BaseAsyncPermission`](api-reference.md#baseasyncpermission) |
| A genuinely async rate limit | [`AsyncSimpleRateThrottle`](api-reference.md#asyncsimpleratethrottle) |
| Keep using existing sync permissions/throttles | Works unchanged - bridged automatically |
