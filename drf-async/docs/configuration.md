# Configuration

This package has no package-specific settings block (no `DRF_ASYNC`
dict to configure) - every class it provides is a drop-in async
equivalent of an existing DRF class, configured the same way: class
attributes on your view (`permission_classes`, `authentication_classes`,
`throttle_classes`, `pagination_class`, `serializer_class`, `queryset`,
...) and the handful of existing DRF-wide settings documented in
[Settings](settings.md).

## Mixing sync and async permission/throttle classes freely

`AsyncAPIView.acheck_permissions()`/`.acheck_throttles()` inspect each
configured class at request time and either `await` it directly (if it
defines `async def has_permission`/`allow_request`) or bridge it
through a thread via `sync_to_async(..., thread_sensitive=True)`. There
is nothing to configure to enable this - it works automatically, so a
single view's `permission_classes` list can freely combine
[`BaseAsyncPermission`](api-reference.md#baseasyncpermission)
subclasses with existing sync `BasePermission` subclasses (e.g.
`IsAuthenticated`), and the same is true for `throttle_classes`.

## Registering async-native throttles

[`AsyncSimpleRateThrottle`](api-reference.md#asyncsimpleratethrottle)
subclasses read their rate the same way DRF's own
`SimpleRateThrottle` does - via `scope` and the project-wide
`DEFAULT_THROTTLE_RATES` setting:

```python
# settings.py
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_RATES": {
        "burst": "10/min",
    },
}
```

```python
# throttles.py
from drf_async import AsyncSimpleRateThrottle


class BurstRateThrottle(AsyncSimpleRateThrottle):
    scope = "burst"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}
```

Set `.rate` directly on a subclass instead if you don't want a
project-wide setting entry at all - `scope`/`DEFAULT_THROTTLE_RATES`
are only consulted when `.rate` isn't already set. See
[Settings](settings.md).

## Pagination

`AsyncGenericAPIView.apaginate_queryset()` reads `pagination_class`
exactly like `GenericAPIView.paginate_queryset()` does, and bridges the
paginator itself (a synchronous, but not I/O-bound-until-evaluated,
class) through a thread:

```python
class ArticleViewSet(AsyncModelViewSet):
    pagination_class = PageNumberPagination
    ...
```

No async-native pagination class is needed - pagination only slices
and counts an already-built queryset, so bridging it through a thread
costs nothing meaningful.
