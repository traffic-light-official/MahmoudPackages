# Quick Start

## Basic replay

```
POST /payments/
Idempotency-Key: key-1
{"amount": 2000}
```

First request: executes normally, `201 Created`, `Idempotent-Replayed:
false`. Any retry with the same key and body: identical `201 Created`,
`Idempotent-Replayed: true`, and the view never re-executes.

## Key reuse with a different body is rejected

```
POST /payments/
Idempotency-Key: key-1
{"amount": 5000}
```

If `key-1` was already used for a `{"amount": 2000}` request, this returns
`422 Unprocessable Entity` — the key is tied to that specific request, not
reusable for a different operation.

## Concurrent retries never double-execute

If a client retries *while the original request is still processing*
(a genuine network-level race, not a sequential retry), the second
request gets `409 Conflict` rather than running the view a second time:

```json
{"detail": "A request with Idempotency-Key 'key-1' is already being processed. Retry after it completes."}
```

The client should back off briefly and retry again — by then the first
request will typically have completed and the retry will get the
replayed response instead.

## Status tracking

```python
from drf_idempotency import get_idempotency_status

get_idempotency_status("key-1")  # "in_progress", "completed", or None
```

Useful for a client polling "is my earlier request done yet?" without
resending the full request body.

## Cleaning up expired records (database backend)

```bash
python manage.py cleanup_expired_idempotency_keys
```

Schedule this via cron or Celery beat — see
[Deployment](deployment.md#scheduling-cleanup). Not needed for
`RedisBackend`, which expires keys natively.

## Custom query parameter... there isn't one

Unlike some of this package's siblings, idempotency keys are always read
from a request *header* (per the Stripe convention this package follows),
never a query parameter or body field — see [FAQ](faq.md#why-a-header-and-not-a-body-field-or-query-parameter).

## Next steps

- [Advanced Usage](advanced-usage.md) — writing a custom backend, using
  Redis, combining with other middleware.
- [Security](security.md) — what this package does and doesn't protect
  against.
