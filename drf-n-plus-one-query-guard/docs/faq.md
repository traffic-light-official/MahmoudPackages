# FAQ

## Does this replace `django-debug-toolbar`?

No - they solve different problems. `django-debug-toolbar` is an
interactive, browser-based inspector for one request at a time,
intended for a human looking at it. This package is a programmatic
assertion/detection tool meant for tests and automated gating - it has
no UI, and is designed to be asserted on in CI, not read by eye.
Nothing stops you from using both.

## Does it require `settings.DEBUG = True` to work?

No - unlike reading `connection.queries` (which only populates when
`DEBUG` is `True`, or inside `django.test.utils.CaptureQueriesContext`),
this package uses `connection.execute_wrapper()`, which works
identically regardless of `DEBUG`. The one place `DEBUG` matters is
`NPlusOneGuardMiddleware`'s response header, which is deliberately
gated on `DEBUG` for safety - see [Security](security.md).

## Why does it detect a violation even though the total query count seems reasonable?

Total query count and "does a specific shape repeat" are different
questions. Ten total queries could be ten genuinely distinct queries
(fine) or one query repeated ten times (an N+1) - this package answers
the second question specifically, which is what actually indicates a
missing `select_related`/`prefetch_related`. See
[Architecture](architecture.md#why-fingerprinting-not-a-query-count-budget).

## Can it detect N+1s across `prefetch_related`, not just `select_related`?

Yes, indirectly: `prefetch_related` issues one *additional* query
total (not one per row) to fetch the related objects in bulk, so a
correctly prefetched relationship produces no repeated fingerprint at
all. If you forget `prefetch_related` on a reverse FK/M2M, iterating and
accessing that relation per row produces exactly the same repeated
fingerprint pattern this package already detects - no special handling
needed for "many" relations versus "one" relations.

## Does it work with a custom/third-party model manager or a raw `.raw()`/`.extra()` query?

Yes - detection happens at the database driver boundary
(`connection.execute_wrapper()`), below the ORM's manager/queryset
layer entirely. Any SQL that reaches the database through Django's
connection - regardless of what ORM API produced it, including raw SQL
via `cursor.execute()` directly - is captured and fingerprinted the same
way.

## Does it work with `django.db.transaction.atomic()`?

Yes - transactions don't change how queries reach the database
connection, so `execute_wrapper()` captures everything inside an atomic
block exactly as it would outside one.

## Can I use this outside Django REST Framework, with plain Django views?

Yes - nothing about `QueryTracker`, `NPlusOneGuard`, or
`assert_no_n_plus_one()` is DRF-specific; they operate on Django's
database layer directly. `guard_view()` and
`NPlusOneGuardMiddleware` work equally well wrapping a plain
function-based view. The package is named for its primary intended use
case (DRF API endpoints), not a hard dependency boundary.

## What's the difference between `guard_view()` and just using `NPlusOneGuard` directly in the view body?

None functionally - `guard_view()` is a thin `functools.wraps`-preserving
decorator around exactly `with NPlusOneGuard(...): return func(...)`.
Use whichever reads better for your view; `guard_view()` keeps the
guard visible in the method signature/decorator list rather than nested
inside the body.

## Why doesn't `assert_no_n_plus_one()` read the `N_PLUS_ONE_GUARD` setting?

By design - see
[Configuration](configuration.md#why-assert_no_n_plus_one-ignores-n_plus_one_guard).
