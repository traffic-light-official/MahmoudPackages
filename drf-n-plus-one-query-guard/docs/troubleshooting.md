# Troubleshooting

## `assert_no_n_plus_one()` fails but I don't understand which query is the problem

Read `assertion.violations` for the full detail rather than only the
raised message - keep a reference to the context manager object:

```python
assertion = assert_no_n_plus_one()
with assertion:
    api_client.get("/articles/")
# after a failure, assertion.violations has every Violation found,
# including .sample_sql and .call_sites (every distinct location, not
# just the first).
```

Also check `violation.call_site` points at your own serializer/view
code, not a generic Django internals path - if it doesn't, see the next
entry.

## The reported call site is unhelpful (points at Django/DRF internals, or `<unknown>`)

`_first_application_frame()` filters out frames under
`/site-packages/`, `/django/`, `/rest_framework/`, and this package's
own source directory - a documented heuristic, not a guarantee (see
[Architecture](architecture.md#identifying-the-call-site)). If your
project's own code happens to live under a path containing one of
those substrings (e.g. a vendored `django` directory in your own
project layout), the heuristic can misfire. In that case, use
`violation.sample_sql` (the actual query text, including the table
name) to identify the offending relationship instead of relying on the
call site.

## `ImproperlyConfigured: The 'N_PLUS_ONE_GUARD' Django setting must be a dict`

`N_PLUS_ONE_GUARD` must be a `dict`, even if empty:
`N_PLUS_ONE_GUARD = {}`.

## `ImproperlyConfigured: 'N_PLUS_ONE_GUARD["THRESHOLD"]' must be at least 2`

A `THRESHOLD` of `1` (or `0`) is rejected - a single query execution is
never, by definition, a "repeat." Use `2` (the default - any repeat at
all) or higher.

## `ImproperlyConfigured: ... contains an invalid regular expression`

An entry in `IGNORE_PATTERNS` isn't valid Python regex syntax - the
error message includes the underlying `re.error` detail. Test the
pattern standalone: `python -c "import re; re.compile('your-pattern')"`.

## The middleware doesn't seem to do anything

1. Confirm `drf_n_plus_one_query_guard.middleware.NPlusOneGuardMiddleware`
   is actually listed in `MIDDLEWARE`, not just `INSTALLED_APPS` -
   they're separate settings.
2. If expecting the response header, confirm `settings.DEBUG = True` -
   it is never added otherwise, regardless of `MODE` (see
   [Security](security.md)).
3. If expecting a raised exception, confirm `MODE = "raise"` is set -
   the default is `"warn"`, which never raises.

## A view I know has an N+1 doesn't trigger the guard

1. Confirm the queryset is actually evaluated (iterated, sliced,
   `list()`-ed) inside the guarded scope - a lazy, unevaluated queryset
   executes no query at all until it's consumed.
2. Confirm the repeated access actually happens per-row inside the
   guarded scope, not in a separate, later request/test.
3. Check whether the query is being served from Django's own
   queryset-level cache (e.g. calling `.all()` twice on an
   already-evaluated queryset re-uses cached results without hitting
   the database again) - this isn't an N+1 if no second query actually
   executes.

## Tests fail with `AppRegistryNotReady`

If you're extending this package and add a new top-level import to
`drf_n_plus_one_query_guard/__init__.py`, keep in mind this package
defines no models at all, so eager imports are always safe here -
`AppRegistryNotReady` would indicate a new dependency was introduced
that itself touches models before the app registry is ready; check
what you imported, not this package's own existing modules.
