# FAQ

## Do I have to convert every view in my project to async?

No - sync and async views coexist freely in the same project, even
behind the same ASGI server (see
[Deployment](deployment.md#mixed-syncasync-views-in-the-same-project)).
Convert the views that actually benefit (I/O-heavy, high-concurrency
endpoints) and leave the rest as plain DRF views.

## Does this package make my views faster?

Not automatically, and not by itself for a single request - one async
request against a fast database still takes about as long as its sync
equivalent. The benefit is concurrency: many in-flight requests can
share one event loop instead of each tying up a whole worker/thread for
the duration of their I/O waits, which shows up as better throughput
under concurrent load, not a faster individual response. See
[Performance](performance.md).

## Do I need to rewrite my serializers to be async?

No - `serializer.is_valid()`/`.save()` are called through
`sync_to_async` inside the default `aperform_create`/`aperform_update`,
exactly as-is. Only override them yourself (see
[Advanced Usage](advanced-usage.md#writing-a-genuinely-async-createupdatedestroy))
if you want to skip the serializer's own save step and use the async
ORM directly - not required for correctness, only for avoiding an
extra thread hop.

## Why are the CRUD action methods named `list`/`create`/etc. and not `alist`/`acreate`?

Because DRF's routers (`SimpleRouter`/`DefaultRouter`) hardcode those
exact strings when binding a viewset's actions - see
[Architecture](architecture.md#why-the-crud-action-methods-are-named-listcreate-and-not-alistacreate).

## Can I use a third-party permission or throttle class I don't control?

Yes, unchanged - any `BasePermission`/`BaseThrottle` subclass (sync,
since that's what nearly all third-party ones are) is bridged through a
thread automatically; there is nothing to configure, wrap, or subclass
to make it work with `AsyncAPIView`.

## Does this package work with Django Channels?

They solve different problems and don't directly interact: this
package is about DRF's request/response view layer (`APIView`,
`GenericAPIView`, viewsets) becoming genuinely async; Channels is about
long-lived WebSocket/protocol connections via `AsyncConsumer`. A
project can use both side by side (REST endpoints via this package,
WebSocket endpoints via Channels), sharing the same async ORM calls and
the same ASGI application entry point, but this package does not
provide or require a Channels dependency.

## Does this package support GraphQL (Strawberry, Graphene)?

No - it's specifically built on top of `rest_framework.views`/
`generics`/`mixins`/`viewsets`. A GraphQL library's own async support
(most modern ones have their own) is unrelated to this package.

## What Django versions/backends actually support the async ORM calls this package relies on?

Django 4.2+ for every first-party database backend
(PostgreSQL/MySQL/SQLite/Oracle) - this is also this package's own
minimum supported Django version, precisely because there is no
sensible fallback for a Django version where the async ORM/cache API
doesn't exist yet. See [Installation](installation.md#why-the-django-floor-is-42).

## Why doesn't `AsyncGenericAPIView` provide an async-native pagination class?

By design, not oversight - see
[Architecture](architecture.md#pagination-is-bridged-not-reimplemented).

## Is `drf-async` a replacement for Django Ninja / FastAPI?

No - it's an in-place upgrade path for an existing DRF codebase that
wants real async views without rewriting the whole framework layer
underneath it. If you're starting a new project with no existing DRF
investment, an async-native framework built from scratch around async
may be a better fit; this package's value is specifically for projects
already using DRF.
