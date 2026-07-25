# Configuration

This package has one Django setting, `SERIALIZER_PROFILER`, with five
keys - see [Settings](settings.md) for all of them. Everything else is
configured by mixing `ProfileSerializerMixin`/`ProfileSerializerViewMixin`
into the specific serializers/views you want profiled - there is no
global "profile everything" switch, by design (see
[Performance](performance.md)).

## Two independent mechanisms

This package offers two ways to find slow fields, controlled by
separate settings, usable independently or together:

1. **On-demand header** (`ENABLED`/`RESTRICT_TO_STAFF`/`HEADER_NAME`):
   an opt-in, staff-restricted `X-Serializer-Profile` response header -
   for interactive debugging of one specific request.
2. **Passive logging** (`LOG_SLOW_FIELDS`/`SLOW_FIELD_THRESHOLD_MS`):
   logs a warning whenever any field's total time meets or exceeds a
   threshold, entirely independent of the header mechanism and never
   exposed over HTTP - safe to leave on in production for ongoing
   monitoring.

## The on-demand header

```python
SERIALIZER_PROFILER = {
    "ENABLED": True,
    "RESTRICT_TO_STAFF": True,  # the default
    "HEADER_NAME": "X-Serializer-Profile",  # the default
}
```

With the default `RESTRICT_TO_STAFF: True`, the header is only
attached when `request.user` is authenticated and `is_staff`. See
[Security](security.md) before setting it to `False`.

## Passive slow-field logging

```python
SERIALIZER_PROFILER = {
    "LOG_SLOW_FIELDS": True,
    "SLOW_FIELD_THRESHOLD_MS": 10.0,  # log fields at or above 10ms
}
```

Logged via Python's standard `logging` module under the logger name
`"drf_serializer_performance_profiler"` - configure a handler for it
the same way you would for any other application logger. This
mechanism works even with `ENABLED: False` and regardless of
`RESTRICT_TO_STAFF`, since nothing about it is ever exposed to a
client.
