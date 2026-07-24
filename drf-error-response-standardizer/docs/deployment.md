# Deployment

## Checklist

- [ ] `EXCEPTION_HANDLER` set to
      `drf_error_response_standardizer.handler.problem_details_exception_handler`.
- [ ] `CorrelationIdMiddleware` installed near the top of `MIDDLEWARE`.
- [ ] `CATCH_ALL_EXCEPTIONS` left at its default (`True`) in production,
      so uncaught exceptions never surface a Django debug page or a bare
      500 with no body to API clients.
- [ ] `SERVER_ERROR_DETAIL` reviewed - the default is safe, but confirm
      any customization does not leak internals (see [Security](security.md)).
- [ ] `TYPE_BASE_URI` set if you publish real problem-type documentation
      pages; left `None` (the default) is a perfectly valid production
      configuration.
- [ ] If using `drf-spectacular`, `problem_details_postprocessing_hook`
      added to `SPECTACULAR_SETTINGS["POSTPROCESSING_HOOKS"]` so
      generated docs/SDKs reflect real error responses.
- [ ] Reverse proxies / gateways in front of the API are configured to
      forward (not strip) `X-Correlation-ID` and `traceparent` headers,
      if you rely on caller-supplied correlation across services.

## Behind a reverse proxy or API gateway

`CorrelationIdMiddleware` trusts the incoming `X-Correlation-ID` and
`X-Request-ID` headers verbatim - it does not attempt to distinguish a
value set by a trusted upstream gateway from one set by an untrusted
client. If your deployment is directly internet-facing (no gateway that
strips/overwrites these headers before they reach Django), be aware
that clients can set these to any string; this is safe by design (see
[Security](security.md#correlationrequesttrace-ids-are-not-secrets)) but
means you should not assume uniqueness or any particular format when
using these values as, say, a cache key.

## Structured logging integration

Add the IDs to every log line via a logging filter, so error responses
can be correlated with application logs:

```python
# settings.py
LOGGING = {
    "version": 1,
    "filters": {
        "correlation_id": {
            "()": "myproject.logging.CorrelationIdFilter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["correlation_id"],
        },
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}
```

```python
# myproject/logging.py
import logging

from drf_error_response_standardizer.middleware import get_correlation_id


class CorrelationIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        request = getattr(record, "request", None)
        record.correlation_id = get_correlation_id(request) if request else None
        return True
```

## Multi-region / multi-language deployments

`activate_for_request()` resolves language per request from
`Accept-Language`, so no per-region configuration is required beyond
setting `LANGUAGES` in Django settings and providing compiled `.po`
translations for the locales you support - see
[Advanced Usage](advanced-usage.md#localization).

## Zero-downtime rollout

This package's response shape is purely additive relative to DRF's
default handler for existing clients that only read `detail` (the
`detail` key is always present for validation single-message and
generic-exception cases, and present for most others too) - but clients
parsing DRF's raw field-name-keyed validation error dicts will need to
be updated to read the new `errors` array first. Roll out
`STANDARDIZED_ERRORS_COMPAT=True` (or keep serving the old handler on a
feature flag) during a transition window if you cannot update all
clients atomically.
