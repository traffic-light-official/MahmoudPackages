# drf-idempotency

Stripe-style `Idempotency-Key` support for Django REST Framework: retry a
`POST`/`PATCH`/`PUT` safely and get back the exact same response, with no
risk of double-processing — even under concurrent retries.

## Why this exists

Networks fail. Clients time out and retry. Without idempotency keys, a
retried `POST` can create a duplicate resource — a double charge, a
duplicate order, a second email sent. This package brings Stripe's
`Idempotency-Key` pattern to any Django REST Framework project: attach a
client-generated key to a request, and any retry with that same key
returns the exact original response without re-executing the view.

```
POST /payments/ HTTP/1.1
Idempotency-Key: 6f7a1e3e-2c9d-4b1a-9d0a-6a6f2b6b9b3a

{"amount": 2000, "currency": "usd"}
```

## Where to go next

- New to the package? Start with [Getting Started](getting-started.md).
- Choosing a storage backend? See [Configuration](configuration.md).
- Want the full picture of how race conditions are prevented? Read
  [Architecture](architecture.md).
- Something not behaving as expected? Check [Troubleshooting](troubleshooting.md).

## At a glance

| Task | Where |
| --- | --- |
| Apply idempotency project-wide | [`IdempotencyMiddleware`](api-reference.md#idempotencymiddleware) |
| Apply idempotency to one view | [`@idempotent`](api-reference.md#idempotent) |
| Check a key's status | [`get_idempotency_status`](api-reference.md#get_idempotency_status) |
| Use Redis for storage | [`RedisBackend`](advanced-usage.md#using-the-redis-backend) |
| Use the database for storage | [`DatabaseBackend`](advanced-usage.md#using-the-database-backend) |
| Write a custom backend | [`BaseBackend`](api-reference.md#basebackend) |
| Clean up expired database records | `python manage.py cleanup_expired_idempotency_keys` |
