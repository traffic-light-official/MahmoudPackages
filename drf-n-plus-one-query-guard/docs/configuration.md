# Configuration

All project-wide configuration lives under a single Django setting,
`N_PLUS_ONE_GUARD` - see [Settings](settings.md) for the complete
reference. `assert_no_n_plus_one()` deliberately does **not** read this
setting (see below); everything else (`NPlusOneGuard`,
`NPlusOneGuardMiddleware`, `guard_view()`) does, with per-call overrides
available everywhere threshold/mode make sense.

## Choosing a threshold

`THRESHOLD` (default `2`) is the minimum number of times an identical
query fingerprint must repeat to be reported. `2` - "any repeat at
all" - is the right default for most projects: a genuinely repeated
identical query shape is very rarely intentional in a single request. Raise
it only if your project has a specific, common pattern of a small,
fixed number of legitimate repeats (rare) - prefer `IGNORE_PATTERNS` for
a specific known-acceptable query instead of raising the threshold
globally.

## Choosing a mode

- `"warn"` (default): logs each violation via the standard `logging`
  module. Safe everywhere, including production - it never changes a
  response or raises.
- `"raise"`: raises `NPlusOneDetectedError`. Use in development, CI, and
  tests - never in production (see [Security](security.md)).
- `"report"`: does nothing automatically; read `.violations` yourself.
  What `NPlusOneGuardMiddleware` effectively uses internally to decide
  whether to add its response header.

## Why `assert_no_n_plus_one()` ignores `N_PLUS_ONE_GUARD`

Test assertions should be explicit and self-contained, not dependent on
ambient project configuration that could change under them - a
`THRESHOLD` tuned for production `warn`-mode logging noise reduction
should not silently loosen what your tests actually assert. Pass
`threshold=`/`ignore_patterns=` directly to `assert_no_n_plus_one()` if
you need something other than its own default of `2`.

## Ignoring a specific known-acceptable repeated query

```python
N_PLUS_ONE_GUARD = {
    "IGNORE_PATTERNS": [r"myapp_taggeditem"],
}
```

Matched via `re.search` against the normalized SQL text - see
[Common Patterns](common-patterns.md#ignoring-a-specific-known-acceptable-query).
