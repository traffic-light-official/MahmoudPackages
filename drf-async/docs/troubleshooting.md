# Troubleshooting

## `ValueError: <view> returned an unawaited coroutine instead of HttpResponse`

The view (or one of its bound actions, for a viewset) is `async def`
but Django's async handler called it synchronously - it never got
marked as an async-compatible callable. This happens if you subclass
`AsyncGenericViewSet` (or `AsyncModelViewSet`/`AsyncReadOnlyModelViewSet`,
which both inherit its `as_view()`) but bind a mix of sync and async
actions in the same `as_view()` call (e.g. one plain sync `@action`
alongside the async CRUD methods) - the override only marks the whole
view async when *every* bound action is a coroutine function. Make
every action on that viewset async, or split the sync one into a
separate, plain sync view. See
[Architecture](architecture.md#why-as_view-needs-an-override).

## `SynchronousOnlyOperation: You cannot call this from an async context`

Something reached the database (or another sync-only Django API)
directly from inside an `async def` method without going through
`sync_to_async`. Common causes:

- A custom `aperform_create`/`aperform_update` override that calls
  `serializer.save()` directly instead of
  `await sync_to_async(serializer.save, thread_sensitive=True)()`.
- A test fixture that calls `Model.objects.create(...)` directly inside
  an `async def` test function - see
  [Testing](testing.md#async-fixtures-for-creating-test-data).
- Accessing `request.user` synchronously somewhere in your own code
  before `AsyncAPIView.aperform_authentication` has run (rare, since
  `dispatch()` calls it early, but possible if a custom `ainitial()`
  override reorders things).

## My permission's `message` is being replaced with a generic one

DRF's `permission_denied()` raises `NotAuthenticated` - not your
permission's own `message` - whenever at least one authenticator is
configured but none of them authenticated the request, regardless of
which permission actually denied it. If a view's `permission_classes`
includes a genuinely denying permission (like
`BaseAsyncPermission`-based `HasValidApiKey`) but the client saw
`"Authentication credentials were not provided."` instead of your
permission's message, set `authentication_classes: list[type] = []` on
that view (or remove authenticators from `DEFAULT_AUTHENTICATION_CLASSES`
project-wide, if that's actually your intent) - see
[Security](security.md#authentication_classes-changes-which-message-a-client-sees-not-who-is-authorized).

## Two different test clients seem to share the same throttle limit

`AsyncSimpleRateThrottle`'s cache-based state persists across tests
unless explicitly cleared - add an autouse fixture:

```python
@pytest.fixture(autouse=True)
def _clear_cache():
    from django.core.cache import cache
    cache.clear()
```

## Data from one async test appears in an unrelated later test

Classic symptom of the `django_db(transaction=True)` gap explained in
[Testing](testing.md#the-one-thing-you-must-get-right-use-transactiontrue-for-async-database-tests) -
a row a previous `async def` test created via a `sync_to_async`-bridged
call escaped its transaction because it ran on a different thread. Add
`transaction=True` to that test's `django_db` marker (or the whole
file's `pytestmark`).

## `AttributeError` (or a confusing failure) passing `REMOTE_ADDR=...`/other WSGI-style kwargs to `AsyncClient`

`AsyncClient`/`AsyncRequestFactory` are ASGI-based - they don't accept
the WSGI environ-style keyword arguments a sync `Client`/
`RequestFactory` does (`REMOTE_ADDR=`, `HTTP_X_FOO=`). Use the
`headers={}` dict parameter for custom headers, and test client-IP
logic via a header your own code reads instead of trying to fake
`REMOTE_ADDR` - see
[Testing](testing.md#testing-with-djangotestasyncclient).

## A header I set with `HTTP_X_CLIENT_ID="..."` shows up doubled (`HTTP_HTTP_X_CLIENT_ID`)

That's the WSGI kwarg convention, which doesn't apply to `AsyncClient`.
Use `client.get(path, headers={"X-Client-Id": "..."})` instead.

## `415 Unsupported Media Type` from `AsyncRequestFactory.put()`/`.patch()`

Unlike `.post()`, `.put()`/`.patch()` don't auto-encode a `data={}`
dict as multipart form data - pass an explicit
`content_type="application/json"` alongside `json.dumps(data)`.

## `NotSupportedError` (or similar) raised from an async ORM call

The configured database backend doesn't implement Django's async
interface. All first-party backends do as of Django 4.2 - this
typically only happens with a third-party backend that hasn't been
updated; check that backend's own release notes.
