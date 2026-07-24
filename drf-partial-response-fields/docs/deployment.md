# Deployment

## There is nothing to deploy

This package adds no processes, no background workers, no cache backend,
and no database tables. It is pure Python that runs inside your existing
Django/DRF request-response cycle. "Deploying" it is exactly the same as
deploying any other pip dependency: pin it in `requirements.txt` /
`pyproject.toml`, install it, restart your app servers.

## Version pinning

```
drf-partial-response-fields>=1.0,<2.0
```

Pin to a major version range. Any breaking change bumps the major version
per [Semantic Versioning](https://semver.org/), with a migration note in
`CHANGELOG.md`.

## Supported runtime versions

| Dependency | Supported |
| --- | --- |
| Python | 3.10, 3.11, 3.12, 3.13 |
| Django | 4.2, 5.0, 5.1, 5.2 |
| Django REST Framework | 3.14+ |

Verify your specific combination is covered by the CI matrix in
[`.github/workflows/ci.yml`](https://github.com/mahmoudgshaker/drf-partial-response-fields/blob/main/.github/workflows/ci.yml)
before upgrading Python or Django in production.

## Rolling out to an existing high-traffic API

1. Add the mixins to serializers/views behind a feature flag or on a
   staging environment first.
2. Compare query counts before/after using
   [`docs/performance.md#benchmarking-your-own-views`](performance.md#benchmarking-your-own-views)
   against your actual models — the automatic optimizer's behavior depends
   on your specific relation shapes.
3. Roll out with `ENABLE_QUERY_OPTIMIZATION = False` first if you want the
   output-filtering behavior without the queryset changes initially, then
   enable optimization once you've confirmed the filtering behaves as
   expected.
4. Set `MAX_DEPTH` / `MAX_FIELDS_LENGTH` deliberately for public-facing
   deployments — see [Security](security.md).

## Multi-region / multi-tenant deployments

Nothing in this package is aware of tenancy or region. It operates purely
on the queryset and serializer you already have per-request; any
tenant-scoping you apply in `get_queryset()` composes normally (see
[Advanced Usage](advanced-usage.md#combining-with-django-filter-custom-get_queryset)).

## Observability

There is no built-in logging or metrics emission — the package is a pure
transformation of serializer fields and querysets, with predictable,
synchronous behavior. If you want visibility into how often `?fields=` is
used and what it saves, instrument at the view layer (e.g. a middleware
recording `request.GET.get("fields")` and the resulting query count via
`django.db.connection.queries` in `DEBUG` mode, or your APM's query-count
metric).
