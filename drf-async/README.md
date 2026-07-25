# drf-async

[![PyPI version](https://img.shields.io/pypi/v/drf-async.svg)](https://pypi.org/project/drf-async/)
[![Python versions](https://img.shields.io/pypi/pyversions/drf-async.svg)](https://pypi.org/project/drf-async/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

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

## Why

DRF's `APIView.dispatch()` calls the resolved handler method
synchronously - `response = handler(request, *args, **kwargs)`. Define
`async def get(self, request)` on a plain `APIView` and this assigns an
unawaited coroutine as the "response," breaking immediately. This
package provides a `dispatch()` that's a real coroutine throughout,
correctly bridging DRF's synchronous permission/throttle/serializer
internals (which may touch the database) through a thread via
`sync_to_async`, while your own handler code and queryset access use
Django's real async ORM (`aget`, `acreate`, `aiterator`, `async for`) -
stable since Django 4.2 - directly, with no thread hop at all.

## Features

- **`AsyncAPIView`**: async-native `dispatch()`/`initial()` - permission
  and throttle classes may be classic sync ones (auto-bridged) or
  genuinely async ones, mixed and matched freely.
- **`AsyncGenericAPIView`** + 9 concrete generic views
  (`AsyncListAPIView`, `AsyncCreateAPIView`, etc.) mirroring
  `rest_framework.generics` one-to-one.
- **`AsyncModelViewSet`**/`AsyncReadOnlyModelViewSet`/`AsyncGenericViewSet`
  - action methods named identically to DRF's own sync mixins, so
    `DefaultRouter`/`SimpleRouter` route to them with **no special
    router** needed.
- **`BaseAsyncPermission`**: write a permission check as a native
  coroutine (e.g. calling an external auth service) with no thread hop.
- **`BaseAsyncThrottle`/`AsyncSimpleRateThrottle`**: a genuinely
  async-native rate throttle using Django's async cache API
  (`cache.aget`/`aset`), not a bridged sync one.
- **Existing sync permission/throttle classes keep working unchanged** -
  bridged automatically via `sync_to_async(..., thread_sensitive=True)`.
- **Fully typed**, PEP 561 compatible, `mypy --strict` clean.

## Installation

```bash
pip install drf-async
```

Requires Python 3.10+, Django 4.2-5.2 (for the async ORM/cache APIs
this package relies on), and Django REST Framework 3.14+. Serve your
project via an ASGI server (e.g. `uvicorn`/`daphne`/`hypercorn`) to
actually benefit from async views - `AsyncAPIView` still works under
WSGI, but Django wraps each async view in its own event loop per
request in that case, which defeats the concurrency benefit.

## Quick Start

```python
from drf_async import AsyncAPIView
from rest_framework.response import Response


class PingView(AsyncAPIView):
    async def get(self, request, *args, **kwargs):
        return Response({"pong": True})
```

```python
from drf_async import AsyncModelViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("articles", ArticleViewSet)
```

See [`docs/quickstart.md`](docs/quickstart.md) for async permissions,
async throttles, and writing a genuinely async `create`/`update`.

## Documentation

Full documentation is available at
[Documentation Home Page](https://mahmoudgshake.github.io/MahmoudPackages/drf-async/), including:

- [Getting Started](https://mahmoudgshake.github.io/MahmoudPackages/drf-async/getting-started)
- [Installation](https://mahmoudgshake.github.io/MahmoudPackages/drf-async/installation)
- [Configuration](https://mahmoudgshake.github.io/MahmoudPackages/drf-async/configuration) / [Settings](https://mahmoudgshake.github.io/MahmoudPackages/drf-async/settings)
- [Quick Start](https://mahmoudgshake.github.io/MahmoudPackages/drf-async/quickstart)
- [Advanced Usage](https://mahmoudgshake.github.io/MahmoudPackages/drf-async/advanced-usage)
- [Architecture](https://mahmoudgshake.github.io/MahmoudPackages/drf-async/architecture)
- [API Reference](https://mahmoudgshake.github.io/MahmoudPackages/drf-async/api-reference)
- [Examples](https://mahmoudgshake.github.io/MahmoudPackages/drf-async/examples)
- [Common Patterns](https://mahmoudgshake.github.io/MahmoudPackages/drf-async/common-patterns)
- [Performance](https://mahmoudgshake.github.io/MahmoudPackages/drf-async/performance)
- [Security](https://mahmoudgshake.github.io/MahmoudPackages/drf-async/security)
- [Testing](https://mahmoudgshake.github.io/MahmoudPackages/drf-async/testing)
- [Deployment](https://mahmoudgshake.github.io/MahmoudPackages/drf-async/deployment)
- [FAQ](https://mahmoudgshake.github.io/MahmoudPackages/drf-async/faq)
- [Troubleshooting](https://mahmoudgshake.github.io/MahmoudPackages/drf-async/troubleshooting)

## Contributing

Contributions are welcome — see [Contributing](https://mahmoudgshake.github.io/MahmoudPackages/drf-async/contributing).

## License

MIT — see [LICENSE](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-async/LICENSE).
