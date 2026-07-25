# Deployment

## Checklist

- [ ] `drf_serializer_performance_profiler` in `INSTALLED_APPS`.
- [ ] `SERIALIZER_PROFILER["ENABLED"]` is `False` (the default) in
      production, or its `True` override is a deliberate,
      environment-gated decision, not an accidental leftover from local
      debugging - see [Security](security.md).
- [ ] `RESTRICT_TO_STAFF` is `True` (the default) in any environment
      with real user accounts.
- [ ] If using `LOG_SLOW_FIELDS` for ongoing monitoring, a log handler
      is actually configured for the `"drf_serializer_performance_profiler"`
      logger - otherwise the warnings are generated but go nowhere.

## No database migrations, no persisted state

This package defines no models - there is nothing to migrate, and no
state persists between requests or between processes. Every profile is
built fresh per-request and discarded once the response is sent
(unless you explicitly read and store it yourself).

## Safe to leave installed with both settings off

With `ENABLED: False` and `LOG_SLOW_FIELDS: False` (both defaults),
mixing `ProfileSerializerMixin` into a serializer costs a single
settings lookup pair per `to_representation()` call and exposes
nothing over HTTP - there's no need to conditionally install this
package per-environment.

## Enabling `LOG_SLOW_FIELDS` in production

This is the one setting this package's own docs recommend considering
for permanent, production use (unlike the header, which is meant for
targeted debugging) - see
[Performance](performance.md#log_slow_fields-is-meant-to-be-safe-for-continuous-production-use).
Pick `SLOW_FIELD_THRESHOLD_MS` based on your actual latency budget for
the endpoints you're monitoring, not an arbitrary default.
