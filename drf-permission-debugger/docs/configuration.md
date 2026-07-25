# Configuration

This package has one Django setting, `PERMISSION_DEBUGGER`, with four
keys - see [Settings](settings.md) for all of them. Everything else is
configured the same way you'd configure any other DRF view:
`permission_classes` on the viewset itself.

## The master switch: `ENABLED`

```python
# settings.py
PERMISSION_DEBUGGER = {
    "ENABLED": True,
}
```

`ENABLED` (default `False`) gates whether a trace is ever attached to
a response. Tracing itself always runs internally on any view mixing
in `PermissionDebugMixin` (so `get_permission_trace(view)` works from
your own code even with `ENABLED: False`) - this setting only controls
whether anything is exposed over HTTP.

## Who can see the trace: `RESTRICT_TO_STAFF`

```python
PERMISSION_DEBUGGER = {
    "ENABLED": True,
    "RESTRICT_TO_STAFF": True,  # the default
}
```

With the default `True`, the trace header (and body, if
`INCLUDE_IN_RESPONSE_BODY` is also on) is only attached when
`request.user` is authenticated and `is_staff` - never for an
anonymous or non-staff user, regardless of `ENABLED`. Set to `False`
only in an environment with no real, untrusted users - see
[Security](security.md).

## Where the trace goes

```python
PERMISSION_DEBUGGER = {
    "ENABLED": True,
    "HEADER_NAME": "X-Permission-Trace",  # the default
    "INCLUDE_IN_RESPONSE_BODY": False,  # the default
}
```

- `HEADER_NAME`: the response header the compact, single-line trace
  summary is attached to.
- `INCLUDE_IN_RESPONSE_BODY`: when `True`, a **denied** response's JSON
  body additionally gets a `"permission_trace"` key with the full,
  structured per-check list (not just the header's compact summary).
  Never added to a *granted* response, since there's nothing
  interesting to explain there.
