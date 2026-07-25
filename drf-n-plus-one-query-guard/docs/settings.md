# Settings

All configuration lives under a single Django setting,
`N_PLUS_ONE_GUARD`, a dict of overrides merged on top of the defaults
below. Not read by `assert_no_n_plus_one()` - see
[Configuration](configuration.md#why-assert_no_n_plus_one-ignores-n_plus_one_guard).

```python
# settings.py
N_PLUS_ONE_GUARD = {
    "THRESHOLD": 2,
    "MODE": "warn",
}
```

## `THRESHOLD`

- **Type:** `int`
- **Default:** `2`
- **Must be:** at least `2`

The minimum number of occurrences of an identically-fingerprinted query
for it to be reported as a suspected N+1.

## `MODE`

- **Type:** `str`
- **Default:** `"warn"`
- **Must be:** one of `"warn"`, `"raise"`, `"report"`

What happens when a violation is found:

- `"warn"`: logs via the standard `logging` module (see `LOGGER_NAME`).
- `"raise"`: raises `NPlusOneDetectedError`. See
  [Security](security.md) before enabling in anything user-facing.
- `"report"`: does nothing automatically - read `.violations` yourself.

## `LOGGER_NAME`

- **Type:** `str`
- **Default:** `"drf_n_plus_one_query_guard"`

The `logging` logger name used in `"warn"` mode.

## `IGNORE_PATTERNS`

- **Type:** `list[str]`
- **Default:** `[]`

Regular expression patterns, matched via `re.search` against the
normalized SQL text (see [Architecture](architecture.md)). A query
matching any pattern here is never counted toward a violation,
regardless of how many times it repeats. Invalid regexes raise
`ImproperlyConfigured` at settings-access time, not silently at
detection time.

## `RESPONSE_HEADER`

- **Type:** `str`
- **Default:** `"X-N-Plus-One-Warnings"`

The response header name `NPlusOneGuardMiddleware` uses to report
violations, only ever added when `settings.DEBUG` is `True` - see
[Security](security.md).
