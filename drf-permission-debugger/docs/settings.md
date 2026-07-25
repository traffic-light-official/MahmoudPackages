# Settings

All configuration lives under one Django setting,
`PERMISSION_DEBUGGER`, a dict of overrides merged on top of the
defaults below. It's optional - omit it entirely to use all defaults
(which means: tracing runs internally, but nothing is ever exposed
over HTTP).

```python
# settings.py
PERMISSION_DEBUGGER = {
    "ENABLED": True,
    "RESTRICT_TO_STAFF": True,
    "HEADER_NAME": "X-Permission-Trace",
    "INCLUDE_IN_RESPONSE_BODY": False,
}
```

## Keys

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `ENABLED` | `bool` | `False` | Master switch - whether a trace is ever attached to a response. |
| `RESTRICT_TO_STAFF` | `bool` | `True` | When `True`, the trace is only attached for an authenticated, `is_staff` user. See [Security](security.md). |
| `HEADER_NAME` | `str` | `"X-Permission-Trace"` | The response header the compact trace summary is attached to. |
| `INCLUDE_IN_RESPONSE_BODY` | `bool` | `False` | When `True`, a denied response's JSON body also gets a `"permission_trace"` key with the full structured trace. |

## Validation

- `ENABLED`, `RESTRICT_TO_STAFF`, `INCLUDE_IN_RESPONSE_BODY` must be `bool`.
- `HEADER_NAME` must be a non-empty `str`.
- An unknown key raises `ImproperlyConfigured` immediately, naming the
  valid keys.

All four are validated lazily on first access and cached; the cache is
invalidated automatically via Django's `setting_changed` signal, so
`@override_settings(PERMISSION_DEBUGGER={...})` works correctly in
tests - see [Testing](testing.md).

## `get_setting`

```python
from drf_permission_debugger import get_setting

get_setting("ENABLED")  # False, unless overridden
```

Raises `KeyError` for an unrecognized key name, and
`django.core.exceptions.ImproperlyConfigured` if the
`PERMISSION_DEBUGGER` setting itself is malformed.
