# FAQ

## Why a header, and not a body field or query parameter?

This follows Stripe's convention (and the emerging
[IETF draft standard](https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/)
for idempotency keys) for good reason: a header keeps the key entirely
out of your request body's schema, so it never needs to be added to
serializers, validated as a "real" field, or explained in your API's data
model documentation — it's transport-level metadata about the *request*,
not part of the *resource* being created.

## Does this work with GET requests?

By default, no — `METHODS` excludes `GET` since GET is already supposed to
be idempotent/side-effect-free per HTTP semantics. You can add `"GET"` to
`METHODS` if you have a non-compliant GET endpoint with side effects, but
consider fixing the endpoint instead.

## What happens if my view doesn't read `request.body` at all?

Nothing different — fingerprinting still reads `request.body` regardless
of whether your view itself parses the body via `request.data` or
ignores it. Reading `request.body` is safe to do multiple times; Django
caches it after the first read.

## Can I use this with GraphQL or non-DRF Django views?

The middleware works with any Django view (DRF or not), since it operates
at the WSGI/Django request level, not the DRF level. The `@idempotent()`
decorator works with function-based Django views too (not just DRF's
`@api_view`) — see `_find_request()`'s duck-typing in
[Architecture](architecture.md), which just needs `.method` and
`.headers` attributes, both present on any Django `HttpRequest`.

## Does the response include the idempotency key even on the very first (non-replayed) request?

Yes — both `Idempotency-Key` (echoing back what the client sent) and
`Idempotent-Replayed: false` are added to every response this package
processes, not just replayed ones, so clients have one consistent way to
confirm idempotency handling was applied.

## What if two requests with the same key arrive at the exact same instant?

Exactly one wins the race (`acquired=True`) and proceeds; the other gets
`409 Conflict` immediately (no blocking/waiting) — see
[Architecture](architecture.md#the-core-operation-acquire-or-get). The
loser should retry after a short delay, by which point the winner will
typically have completed and the retry will get the replayed response
instead of another conflict.

## Why 409 instead of waiting for the in-progress request to finish?

Blocking would tie up a request-handling thread/worker for however long
the original request takes, and risks resource exhaustion under a retry
storm. Returning `409` immediately keeps this package's behavior fast and
predictable; client-side retry-with-backoff (which any sane HTTP client
should already implement) naturally resolves it.

## Is there a way to manually invalidate/clear a specific key?

Not as public API today — but it's straightforward via the backend
directly if you need it for an operational/debugging scenario:

```python
from drf_idempotency.core import get_backend

get_backend().fail("some-key")  # releases it, as if it had failed
```

## Does this package send any telemetry or make network calls of its own?

No — beyond the storage backend you configure (your own database or
Redis instance), this package makes no network calls and collects no
telemetry.
