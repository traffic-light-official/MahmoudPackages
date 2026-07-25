# Examples

A complete, runnable example lives in [`examples/blog/`](https://github.com/MahmoudGShake/MahmoudPackages/tree/master/drf-async/examples/blog)
in the source repository - models, serializers, views, and a script
that exercises all of them with no test framework and no running
server, just Django configured inline.

Run it yourself:

```bash
git clone https://github.com/MahmoudGShake/MahmoudPackages.git
cd MahmoudPackages/drf-async
pip install -e ".[dev]"
python -m examples.blog.example
```

## `examples/blog/models.py`

```python
from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=200)

    class Meta:
        app_label = "blog"


class Article(models.Model):
    title = models.CharField(max_length=200, unique=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="articles")

    class Meta:
        app_label = "blog"
        ordering = ["id"]
```

## `examples/blog/views.py`

```python
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from drf_async import AsyncAPIView, AsyncModelViewSet, AsyncSimpleRateThrottle, BaseAsyncPermission
from examples.blog.models import Article
from examples.blog.serializers import ArticleSerializer


class PingView(AsyncAPIView):
    permission_classes = [AllowAny]

    async def get(self, request, *args, **kwargs):
        return Response({"pong": True})


class AllowRegisteredClients(BaseAsyncPermission):
    message = "Unknown client."

    async def has_permission(self, request, view):
        return request.headers.get("X-Client-Id") == "trusted-client"


class OncePerMinuteThrottle(AsyncSimpleRateThrottle):
    scope = "example_once_per_minute"
    THROTTLE_RATES = {"example_once_per_minute": "1/min"}

    def get_cache_key(self, request, view):
        ident = request.headers.get("X-Client-Id", "anonymous")
        return self.cache_format % {"scope": self.scope, "ident": ident}


class ArticleViewSet(AsyncModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = ArticleSerializer
    queryset = Article.objects.select_related("author").all()
```

## `examples/blog/example.py` output

The script calls each view directly (`await View.as_view()(request)`),
without a URL conf or a running ASGI server - useful for understanding
what each piece does in isolation, exactly like the walkthrough below.

```text
== PingView ==
  GET /ping/ -> 200 {'pong': True}

== Async-native permission ==
  No X-Client-Id header -> 403 {'detail': ErrorDetail(string='Unknown client.', code='permission_denied')}
  Trusted X-Client-Id header -> 200 {'pong': True}

== Async-native throttle (1/min) ==
  First request -> 200
  Second request (same client) -> 429

== ArticleViewSet: full async CRUD ==
  POST /articles/ -> 201 {'id': 1, 'title': 'Async Views in DRF', 'author': 1}
  GET /articles/ -> 200, 1 article(s)
  GET /articles/1/ -> 200 {'id': 1, 'title': 'Async Views in DRF', 'author': 1}
  PATCH /articles/1/ -> 200 {'id': 1, 'title': 'Async Views in DRF (Updated)', 'author': 1}
  DELETE /articles/1/ -> 204
  Remaining articles: []
```

A few things worth noting from this output:

- The permission-denied response's `detail` is `"Unknown client."` -
  `AllowRegisteredClients`'s own message - only because the example
  sets `authentication_classes = []` on the guarded view. Leave DRF's
  default authenticators enabled and a permission denial gets masked
  by a generic `"Authentication credentials were not provided."`
  instead; see [Troubleshooting](troubleshooting.md#my-permissions-message-is-being-replaced-with-a-generic-one).
- The second throttled request is rejected (`429`) because it reuses
  the same `X-Client-Id` header - a genuinely different client
  (a different header value) would not be throttled by the first
  client's usage.
- `POST`/`PATCH` bridge `serializer.is_valid()`/`.save()` through a
  thread; `list`/`retrieve`/`delete` and the final
  `[article.title async for article in Article.objects.all()]` all use
  Django's async ORM directly - no thread hop at all.

See [Quick Start](quickstart.md) for the same views wired up to a real
URL conf and router instead of being called directly.
