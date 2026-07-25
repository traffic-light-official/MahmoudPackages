# Settings

All configuration lives under one Django setting, `BULK_OPERATIONS`, a
dict of overrides merged on top of the defaults below. It's optional -
omit it entirely to use both defaults.

```python
# settings.py
BULK_OPERATIONS = {
    "MAX_BATCH_SIZE": 500,
    "ATOMIC": False,
}
```

## Keys

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `MAX_BATCH_SIZE` | `int` | `100` | Maximum number of items accepted in a single bulk request. A request submitting more raises [`BatchSizeExceededError`](api-reference.md#batchsizeexceedederror) (`400`) before any item is validated. |
| `ATOMIC` | `bool` | `True` | Whether a whole batch is wrapped in one database transaction (`True`) or every item is processed independently in its own savepoint (`False`). See [Architecture](architecture.md). |

## Validation

- `MAX_BATCH_SIZE` must be a positive integer (`>= 1`).
- `ATOMIC` must be a `bool`.
- An unknown key raises `ImproperlyConfigured` immediately, naming the
  valid keys.

Both are validated lazily on first access and cached; the cache is
invalidated automatically via Django's `setting_changed` signal, so
`@override_settings(BULK_OPERATIONS={...})` works correctly in tests -
see [Testing](testing.md).

## `get_setting`

```python
from drf_bulk_operations import get_setting

get_setting("MAX_BATCH_SIZE")  # 100, unless overridden
```

Raises `KeyError` for an unrecognized key name, and
`django.core.exceptions.ImproperlyConfigured` if the `BULK_OPERATIONS`
setting itself is malformed.
