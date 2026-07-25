# FAQ

## Does this package change the serialized output?

No - never. See
[Architecture](architecture.md#the-core-guarantee-identical-output-to-a-plain-serializer)
for exactly how `to_representation()` is kept line-for-line equivalent
to DRF's own, and `tests/test_mixins.py::TestOutputIsUnchanged` for the
tests proving it against both a disabled run and a completely
undecorated serializer.

## Why is the header missing even though I set `ENABLED: True`?

Almost always `RESTRICT_TO_STAFF` (default `True`) - the requesting
user must be authenticated and `is_staff`. See
[Troubleshooting](troubleshooting.md).

## Does this replace `drf-n-plus-one-query-guard`?

No - they answer different questions. The guard detects *that* a
request triggered a repeated query pattern (fingerprint-based, whole
request scope, works even without this package). This package tells
you *which specific serializer field* is responsible for however many
queries ran, with exact per-field timing alongside it. Use both - see
[Advanced Usage](advanced-usage.md#combining-with-drf-n-plus-one-query-guard).

## Can I profile a serializer that isn't used in a DRF view at all?

Yes - `ProfileSerializerMixin` only needs `ENABLED`/`LOG_SLOW_FIELDS`
to be on; it works the same whether the serializer is instantiated
inside a view, a management command, a Celery task, or a Python shell.
`ProfileSerializerViewMixin` (the response header) does need a real
DRF view, but reading the profile yourself via `get_serializer_profile()`
doesn't.

## Does the query count include queries from `select_related`/`prefetch_related`?

`select_related` produces one bigger `JOIN`ed query at the *queryset*
level, before any serializer field ever runs - it doesn't add to any
field's count. `prefetch_related` runs its own separate query(ies) when
the queryset is evaluated, also before `to_representation()` is called
per instance - so a well-`prefetch_related`d relation correctly shows
`0` additional queries in the profile, which is exactly the signal you
want: the fix (using `prefetch_related`) is reflected as the fix (no
more per-row queries) in the numbers.

## Why does `average_time_ms` differ from `total_time_ms` divided by the number of rows in the response?

It doesn't, normally - `average_time_ms` is defined as exactly
`total_time_ms / call_count`, and `call_count` for a list response
equals the number of rows that field was actually rendered for (not
skipped via `SkipField`). If a field is skipped for some rows (e.g. a
conditionally-included field), `call_count` is smaller than the row
count, which is the one case these two numbers can diverge.

## Is there a way to see this in the Django admin or a debug toolbar panel?

Not built in - this package focuses on the HTTP response header, the
passive logger, and programmatic access
(`get_serializer_profile()`/`merge_profiles()`). A
`django-debug-toolbar` panel built on top of these would be a
reasonable addition; open an issue if you'd like to contribute one (see
[Contributing](contributing.md)).

## Does this work with `django-rest-framework`'s `Serializer` (not `ModelSerializer`)?

Yes - `ProfileSerializerMixin` overrides `to_representation()`, which
both `Serializer` and `ModelSerializer` share identically; nothing in
this package depends on `ModelSerializer`-specific behavior.
