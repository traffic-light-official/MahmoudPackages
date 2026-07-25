# Deployment

## Checklist

- [ ] `drf_n_plus_one_query_guard` in `INSTALLED_APPS` (required for
      `N_PLUS_ONE_GUARD` setting validation - not required at all if
      you only use `assert_no_n_plus_one()` in tests, since it reads no
      Django setting).
- [ ] If using `NPlusOneGuardMiddleware` in production,
      `MODE` is `"warn"` or `"report"` - never `"raise"` - see
      [Security](security.md#never-enable-mode-raise-for-the-middleware-in-production).
- [ ] `"raise"` mode, if used at all, is confined to a test-only or
      CI-only settings module, never the production one - see
      [Common Patterns](common-patterns.md#gating-ci-on-n1s-without-touching-production-behavior).
- [ ] `IGNORE_PATTERNS` entries are reviewed, specific regexes (not
      overly broad ones that would silently hide unrelated future N+1s)
      - see [Configuration](configuration.md#ignoring-a-specific-known-acceptable-repeated-query).
- [ ] If monitoring `"warn"`-mode log output in production, the
      `LOGGER_NAME` logger is actually wired into your logging
      configuration (`LOGGING["loggers"]`) - a default Python logger
      with no configured handler silently drops records past `WARNING`
      in some setups.

## Recommended environment-by-environment configuration

| Environment | `MODE` | Middleware installed? |
| --- | --- | --- |
| Local development | `"warn"` or `"raise"` | Yes - immediate feedback while coding. |
| CI / test suite | `"raise"` | Yes, or per-test `assert_no_n_plus_one()`. |
| Staging | `"raise"` (optional) or `"warn"` | Yes - a safe place to catch what CI missed. |
| Production | `"warn"` or `"report"` | Optional - see [Performance](performance.md#recommended-warnreport-in-production-not-raise). |

## No database migrations, no persisted state

This package defines no models - there is nothing to migrate, and no
state persists between requests or between processes. Adding or
removing it from `INSTALLED_APPS`/`MIDDLEWARE` is immediately effective
and fully reversible with no data migration concerns.

## Multi-process / multi-worker deployments

Nothing in this package requires shared state across worker processes -
`QueryTracker`'s captured events live only in memory for the duration
of one guarded scope (one request, one test, one decorated call) and
are discarded afterward. Nothing to configure differently for
Gunicorn/uWSGI workers, Celery workers, or horizontally-scaled
deployments.
