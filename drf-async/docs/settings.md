# Settings

`drf-async` introduces no new Django or DRF settings of its own -
there is no `DRF_ASYNC = {...}` block to configure. Its classes read
the same, already-existing DRF settings (`REST_FRAMEWORK = {...}` in
`settings.py`) that their synchronous counterparts do.

## Settings this package's classes actually read

| Setting | Read by | Effect |
| --- | --- | --- |
| `DEFAULT_THROTTLE_RATES` | [`AsyncSimpleRateThrottle.get_rate()`](api-reference.md#asyncsimpleratethrottle) | Looked up via `.scope`, identically to DRF's own `SimpleRateThrottle` - only consulted when a subclass hasn't already set `.rate` directly. |
| `URL_FIELD_NAME` | [`AsyncCreateModelMixin.get_success_headers()`](api-reference.md#asynccreatemodelmixin) | The serializer field name used to build the `Location` header after a successful `create()` - defaults to `"url"`, matching DRF's own `CreateModelMixin`. |
| `DEFAULT_PERMISSION_CLASSES` / `DEFAULT_AUTHENTICATION_CLASSES` / `DEFAULT_THROTTLE_CLASSES` | `APIView.get_permissions()`/`get_authenticators()`/`get_throttles()` (unchanged, inherited from DRF) | The project-wide defaults applied whenever a view doesn't set its own `permission_classes`/etc. |
| `DEFAULT_PAGINATION_CLASS` | `GenericAPIView.paginator` (unchanged, inherited from DRF) | Used by [`AsyncGenericAPIView.apaginate_queryset()`](api-reference.md#asyncgenericapiview) whenever a view doesn't set its own `pagination_class`. |

Every other DRF setting (content negotiation, renderer/parser classes,
exception handling, schema generation) is entirely untouched - this
package only replaces the request/response lifecycle
(`dispatch`/`initial` and the CRUD action methods) with async
equivalents, not DRF's configuration surface.

## Nothing to configure to enable sync/async bridging

There is deliberately no setting to "opt in" to bridging a sync
permission/throttle class - `drf_async.compat.call_maybe_async()`
detects whether the configured class is a native coroutine at request
time (`asyncio.iscoroutinefunction`) and either awaits it directly or
bridges it through `sync_to_async(..., thread_sensitive=True)`
automatically. See [Configuration](configuration.md) and
[Architecture](architecture.md).
