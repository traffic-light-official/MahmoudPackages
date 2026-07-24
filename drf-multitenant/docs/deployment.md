# Deployment

`drf-multitenant` adds no infrastructure of its own — no server, no
database, no cache backend, no background worker. It runs inside your
existing Django process using whatever `CACHES`/`DATABASES` you already
have configured. This page covers the deployment-relevant decisions
specific to multi-tenancy.

## DNS and routing for subdomain resolution

If you use `subdomain_resolver`, your infrastructure needs to route
`*.yourdomain.com` to your application (a wildcard DNS record and a
wildcard TLS certificate, or per-tenant certificates provisioned as
tenants are created) and `ALLOWED_HOSTS` must accept the wildcard:

```python
ALLOWED_HOSTS = [".yourdomain.com"]
```

## Database considerations at scale

Shared-schema multi-tenancy means every tenant's data grows in the same
tables. Before this becomes a bottleneck:

- Ensure the tenant FK column is indexed (Django does this automatically).
- Add composite indexes leading with the tenant column for your hot
  query paths (see [Performance](performance.md)).
- Table partitioning by tenant (PostgreSQL declarative partitioning, for
  example) is a database-level concern this package is compatible with
  but does not manage — if you need it, it sits underneath the ORM
  layer this package operates at.

## Zero-downtime migrations

`TenantScopedModel` subclasses are ordinary Django models — standard
Django migration practices apply (add nullable, backfill, then make
required in a separate migration; never rename and change type in the
same migration). Nothing about tenant scoping changes migration safety
practices.

## Rolling out `STRICT` mode changes

If you're introducing this package into an existing project, consider
rolling out with `STRICT = False` first (accepting requests with no
resolved tenant, relying on `IsTenantMember` per-view) while you
identify and fix any endpoints that assumed unscoped access, then switch
to `STRICT = True` (the default, and the recommended steady state) once
you've confirmed every client is sending a resolvable tenant.

## Cache backend in production

`get_tenant_cache()` uses whatever `CACHES["default"]` (or your chosen
alias) already points at — Redis, Memcached, or otherwise. No separate
cache infrastructure is needed for per-tenant namespacing; it's purely a
key-prefixing convention on top of your existing backend.

## Monitoring

Route the `drf_multitenant` logger to your log aggregation/alerting
stack — `unscoped()` calls log at `WARNING` and are worth alerting on in
production (see [Security](security.md)). `TenantMiddleware`'s 400
rejections (no resolvable tenant, under `STRICT` mode) are ordinary
Django `JsonResponse`s and show up in your normal request logs/metrics
like any other 4xx.
