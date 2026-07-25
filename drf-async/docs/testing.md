# Testing

## Running this package's own test suite

```bash
pip install -e ".[test]"
pytest
```

With coverage:

```bash
pytest --cov --cov-report=term-missing
```

Across the full Python/Django support matrix via [tox](https://tox.wiki):

```bash
tox
```

## The one thing you must get right: use `transaction=True` for async database tests

pytest-django's default `@pytest.mark.django_db` wraps each test in an
atomic transaction rolled back afterward, on the assumption that the
test and the code under test share one database connection/thread. An
`async def` test that reaches the database through
`sync_to_async(...)` - which includes every call this package bridges
(permission/throttle checks, `serializer.save()`) and, less obviously,
your own test fixtures if they create data via `sync_to_async` - runs
that database call on a *different* thread than the test function
itself. Because Django keeps one database connection per thread, that
bridged call can end up on a connection outside the test's own atomic
block, so data it commits is not rolled back and leaks into whichever
test runs next.

```python
import pytest

pytestmark = pytest.mark.django_db(transaction=True)  # required for async tests
```

This is not a workaround for a bug in this package - it's an inherent
consequence of thread-per-connection plus bridging through a thread,
and it applies to *any* async test that touches the database through
`sync_to_async`, not just tests that happen to use this package. Using
the plain (non-`transaction=True`) default with async tests will
usually pass in isolation and fail intermittently once run alongside
other tests in the same file or session - exactly the kind of flake
that's expensive to track down after the fact.

## Async fixtures for creating test data

```python
from asgiref.sync import sync_to_async
import pytest


@pytest.fixture
def make_author(db):
    async def _make(name="Ada Lovelace"):
        return await sync_to_async(Author.objects.create, thread_sensitive=True)(name=name)

    return _make


async def test_something(make_author):
    author = await make_author()
    ...
```

Calling a plain sync fixture factory (`Author.objects.create(...)`)
directly from inside an `async def` test raises
`SynchronousOnlyOperation` - wrap it the same way this package's own
bridging functions do.

## Testing with `django.test.AsyncClient`

```python
from django.test import AsyncClient
import pytest

pytestmark = pytest.mark.django_db(transaction=True)


async def test_ping(db):
    client = AsyncClient()
    response = await client.get("/ping/")
    assert response.status_code == 200
```

`AsyncClient` is ASGI-based - it does not accept the WSGI-style kwargs
a sync `Client`/`RequestFactory` does:

- **No `REMOTE_ADDR=...` kwarg.** `AsyncClient` builds an ASGI scope,
  which carries the client address as `scope["client"]`, not a
  `REMOTE_ADDR` environ key - passing `REMOTE_ADDR=` (or any
  unrecognized kwarg) is silently coerced into an ASGI header and
  usually breaks in a confusing way (e.g. `AttributeError` if the value
  isn't a string). Test client-IP-dependent logic (like
  `AsyncAnonRateThrottle`'s `get_ident()`) via a header your own
  `get_cache_key()` reads instead, or don't rely on client IP in tests
  at all.
- **Custom headers use a `headers={}` dict, not `HTTP_X_FOO=...`
  kwargs.** The WSGI convention of passing `HTTP_X_CLIENT_ID="..."` as
  a keyword argument does not translate to ASGI - it produces a
  doubled, wrong header name (`HTTP_HTTP_X_CLIENT_ID`) instead of being
  rejected outright, which is easy to miss. Use
  `client.get(path, headers={"X-Client-Id": "..."})` instead.
- **`.put()`/`.patch()` need an explicit `content_type`.** Unlike
  `.post()`, they don't auto-encode a `data=` dict as multipart -  pass
  `json.dumps(data)` with `content_type="application/json"` explicitly.

## Testing an `AsyncGenericAPIView` subclass directly, without a URL conf

```python
from django.test import AsyncRequestFactory

factory = AsyncRequestFactory()


async def test_retrieve(db, make_article):
    article = await make_article()
    request = factory.get(f"/x/{article.pk}/")
    response = await ArticleDetailView.as_view()(request, pk=article.pk)
    assert response.status_code == 200
```

Useful for testing one concrete generic view or mixin in isolation
without registering routes - the same pattern this package's own
`tests/test_generics.py` uses for all nine concrete generic views.

## Testing permission/throttle bridging directly

```python
from drf_async.permissions import check_permission


async def test_bridges_a_sync_permission():
    assert await check_permission(IsAuthenticated(), request=request, view=view) is False
```

Useful for unit-testing a single permission/throttle class's logic
without going through a full view dispatch.

## Fixtures used by this package's own suite

`tests/test_app` declares `Author`/`Article` models, an
`ArticleSerializer` with an explicit `UniqueValidator` (so tests
exercise the "validation itself may touch the database" bridging
path, not just `.save()`), and one view per feature this package
adds - reuse this shape (real models, `transaction=True` throughout,
a clear-cache autouse fixture for throttle tests) in your own project's
test suite.
