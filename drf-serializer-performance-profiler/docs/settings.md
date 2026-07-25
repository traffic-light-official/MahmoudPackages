# Settings

All configuration lives under one Django setting,
`SERIALIZER_PROFILER`, a dict of overrides merged on top of the
defaults below. It's optional - omit it entirely to use all defaults
(both mechanisms off, no overhead beyond a settings lookup per field).

```python
# settings.py
SERIALIZER_PROFILER = {
    "ENABLED": True,
    "RESTRICT_TO_STAFF": True,
    "HEADER_NAME": "X-Serializer-Profile",
    "LOG_SLOW_FIELDS": False,
    "SLOW_FIELD_THRESHOLD_MS": 5.0,
}
```

## Keys

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `ENABLED` | `bool` | `False` | Master switch for the `X-Serializer-Profile` response header. |
| `RESTRICT_TO_STAFF` | `bool` | `True` | When `True`, the header is only attached for an authenticated, `is_staff` user. See [Security](security.md). |
| `HEADER_NAME` | `str` | `"X-Serializer-Profile"` | The response header the compact profile summary is attached to. |
| `LOG_SLOW_FIELDS` | `bool` | `False` | When `True`, logs a warning for any field whose total time meets or exceeds `SLOW_FIELD_THRESHOLD_MS` - independent of `ENABLED`. |
| `SLOW_FIELD_THRESHOLD_MS` | `float` | `5.0` | The threshold (milliseconds) used by `LOG_SLOW_FIELDS`. |

## Validation

- `ENABLED`, `RESTRICT_TO_STAFF`, `LOG_SLOW_FIELDS` must be `bool`.
- `HEADER_NAME` must be a non-empty `str`.
- `SLOW_FIELD_THRESHOLD_MS` must be a non-negative `int`/`float` (not a
  `bool` - `True`/`False` are rejected explicitly, since a threshold of
  "true" or "false" isn't meaningful even though `bool` is technically
  a subclass of `int` in Python).

An unknown key raises `ImproperlyConfigured` immediately, naming the
valid keys. All five are validated lazily on first access and cached;
the cache is invalidated automatically via Django's `setting_changed`
signal, so `@override_settings(SERIALIZER_PROFILER={...})` works
correctly in tests - see [Testing](testing.md).

## `get_setting`

```python
from drf_serializer_performance_profiler import get_setting

get_setting("SLOW_FIELD_THRESHOLD_MS")  # 5.0, unless overridden
```

Raises `KeyError` for an unrecognized key name, and
`django.core.exceptions.ImproperlyConfigured` if the
`SERIALIZER_PROFILER` setting itself is malformed.
