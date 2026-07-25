# Deployment

## Checklist

- [ ] `drf_bulk_operations` in `INSTALLED_APPS`.
- [ ] `MAX_BATCH_SIZE` set to a value appropriate for your actual use
      case and database capacity, not left at the default without a
      deliberate decision - see [Security](security.md).
- [ ] `ATOMIC` set deliberately for each bulk-enabled viewset's actual
      use case (see [Configuration](configuration.md)) - it's a single
      project-wide setting, so if different viewsets in your project
      genuinely need different behavior, that's a design decision to
      make explicitly, not something to discover after the fact from
      unexpected partial-success behavior in production.
- [ ] Load-tested with a realistic batch size at your database's actual
      connection pool limits - atomic mode holds one transaction open
      for the whole batch, so a large `MAX_BATCH_SIZE` under concurrent
      load can hold more simultaneous connections/locks than the same
      number of individual requests would.

## No database migrations, no persisted state

This package defines no models - there is nothing to migrate, and no
state persists between requests or between processes.

## Reverse proxy / load balancer request body size limits

A large `MAX_BATCH_SIZE` is only useful if your reverse proxy (nginx,
an API gateway, a cloud load balancer) actually allows a request body
large enough to hold that many items - check `client_max_body_size`
(nginx) or your platform's equivalent alongside this package's own
setting; a batch rejected by the proxy before it ever reaches Django
returns a generic `413`/`400` from the proxy, not this package's own
structured error response.

## Timeouts

A large atomic batch's total processing time (validation + one
transaction covering every item's write) needs to fit within whatever
request timeout your deployment enforces (gunicorn's `--timeout`, your
proxy's read timeout, a serverless platform's max execution time) - if
legitimate batches are large enough to risk this, either lower
`MAX_BATCH_SIZE` or switch that endpoint to non-atomic mode (each
item's own savepoint completes independently, so a timeout partway
through still leaves earlier items committed, rather than losing
everything).
