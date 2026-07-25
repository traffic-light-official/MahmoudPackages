# Performance

## The point of this package is to remove thread hops, not add them

Every genuinely I/O-bound operation this package touches
(authentication, `list`/`retrieve`/`create`/`update`/`destroy` against
the queryset, `AsyncSimpleRateThrottle`'s cache reads/writes) uses
Django's native async ORM/cache API directly - `queryset.aget()`,
`async for obj in queryset`, `instance.adelete()`,
`cache.aget`/`.aset()` - with no `sync_to_async` bridge in that path at
all. The only place a thread hop happens by default is where DRF's own
machinery is inherently synchronous: permission/throttle classes you
haven't converted to `BaseAsyncPermission`/`BaseAsyncThrottle`, and
`serializer.is_valid()`/`.save()` inside the default
`aperform_create`/`aperform_update`.

## One worker thread per request, not one per bridged call

Every bridged call within a single request (`aperform_authentication`,
each sync permission/throttle check, `serializer.save()`) goes through
`sync_to_async(..., thread_sensitive=True)` - `thread_sensitive=True`
pins all of a given request's bridged calls to the *same* worker
thread (asgiref's default single-thread executor), not a fresh thread
per call. This matters for correctness (Django's per-thread database
connection handling requires it, see
[Architecture](architecture.md#the-syncasync-bridge-call_maybe_async))
and also keeps thread allocation overhead flat regardless of how many
sync permission/throttle classes a view has configured.

## Async views only pay off under an ASGI server

`AsyncAPIView` works under Django's WSGI handler, but Django wraps each
async view call in its own `asyncio.run()`-equivalent per request in
that case - you get correctness (the view runs, the coroutine gets
awaited), not concurrency, since a WSGI worker still handles one
request at a time regardless of whether that one request's view is
async. The actual benefit - many in-flight requests sharing one event
loop, each yielding control during an `await` on I/O instead of
blocking a whole worker - only exists when the server itself is ASGI.
See [Deployment](deployment.md).

## Bridging a sync permission/throttle costs one thread hop, not a serialization step

`call_maybe_async()` bridges via `sync_to_async`, which schedules the
callable on a real OS thread and awaits its result - there's no
pickling, no IPC, no queue beyond asgiref's own executor. For a cheap,
non-database-touching permission (e.g. `AllowAny`, a simple attribute
check), this thread hop is the dominant cost, not the check itself -
converting such a permission to `BaseAsyncPermission` removes even that
hop, though for a genuinely fast synchronous check the difference is
rarely measurable next to the rest of the request.

## Pagination is bridged deliberately, not left synchronous by oversight

`apaginate_queryset()` bridges DRF's real paginator classes through a
thread rather than reimplementing pagination async-natively - see
[Architecture](architecture.md#pagination-is-bridged-not-reimplemented)
for why this is the right tradeoff, not a missing feature: pagination's
own work (slicing, counting) is cheap, and the actual database round
trip it triggers already goes through the async ORM via
`apaginate_queryset`'s caller.

## Measuring your own view

There is no built-in profiling in this package - use a dedicated
profiling package for DRF serializers, or a plain
`time.perf_counter()`/APM span around the parts you suspect,
the same way you would for a synchronous view. Async views don't
introduce a new profiling methodology, just a different set of things
(thread hops vs. database round trips) worth distinguishing between
when the numbers look surprising.
