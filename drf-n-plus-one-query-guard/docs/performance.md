# Performance

## Per-query overhead is one dict-and-list append, no DB round trip added

`QueryTracker._record()` calls the real `execute()` first, then appends
one `QueryEvent` (a lightweight, `slots=True` frozen dataclass) to an
in-memory list. No extra query, no extra network round trip - the
existing query executes exactly once, exactly as it would without this
package installed.

## Fingerprinting is a single regex substitution

`normalize_sql()` runs one `re.sub()` call per query to collapse
whitespace - no SQL parsing, no tokenization, no literal-stripping (see
[Architecture](architecture.md#why-no-literal-stripping-is-needed) for
why that's unnecessary). Cost is linear in the SQL string's length, the
same order of magnitude as computing its hash.

## Call-site resolution walks the stack once per query

`_first_application_frame()` calls `traceback.extract_stack()` once per
executed query and walks it from the innermost frame outward until it
finds a non-library frame - typically a handful of frames for a normal
DRF view (view → serializer → manager → this package's own wrapper).
This is the single most expensive part of the per-query overhead (stack
extraction has real cost), which is why guarding is opt-in per-scope
(`assert_no_n_plus_one()`, `guard_view()`) or per-request
(`NPlusOneGuardMiddleware`), not always-on for every query in the
process regardless of context.

## Middleware overhead only applies to requests it wraps

`NPlusOneGuardMiddleware` only instruments queries executed during the
request it's currently handling - `ExitStack`-managed
`execute_wrapper()` registration and teardown happens once per request,
not once per query. Un-guarded code paths (management commands, Celery
tasks not explicitly wrapped in `NPlusOneGuard`) pay no overhead at all.

## Recommended: `"warn"`/`"report"` in production, not `"raise"`

Beyond the safety reasoning in [Security](security.md), `"warn"` mode's
per-request overhead (stack walking + fingerprinting) is the same
whether or not you ultimately raise - the cost is in capturing and
fingerprinting queries, not in what you do with the result afterward.
If per-request overhead matters more than production visibility into
N+1s at all, don't install `NPlusOneGuardMiddleware` in production;
rely on `assert_no_n_plus_one()` in tests and `guard_view()` on a
handful of known-hot endpoints instead of guarding every request.

## Test suite overhead

`assert_no_n_plus_one()` adds the same per-query overhead described
above only for the duration of the `with` block - a full test suite
using it only in specific tests (the common case) sees no overhead in
the rest.
