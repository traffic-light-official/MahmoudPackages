# Troubleshooting

## The `X-Serializer-Profile` header never appears, even with `ENABLED: True`

Check, in order:

1. Is `request.user` actually authenticated and `is_staff`? This is
   the default (`RESTRICT_TO_STAFF: True`) gate - an anonymous or
   ordinary (non-staff) user never sees the header regardless of
   `ENABLED`.
2. Does the *serializer* mix in `ProfileSerializerMixin`? Without it,
   nothing is ever recorded, so there's nothing for the view mixin to
   attach.
3. Does the *view* mix in `ProfileSerializerViewMixin`? Without it, the
   profile is recorded but never surfaced as a header.
4. Is `ProfileSerializerMixin` listed *before* the DRF serializer base
   class in the MRO? If listed after, DRF's own `to_representation`
   runs instead of this package's override.

## `KeyError` on `response.headers["X-Serializer-Profile"]` in a test

The header genuinely wasn't attached - see the checklist above. Most
often: forgetting `@override_settings(SERIALIZER_PROFILER={"ENABLED":
True})`, or authenticating as a non-staff user with the default
`RESTRICT_TO_STAFF: True`.

## A field's query count is always `0`, even though I expect it to query the database

Check whether the field's query already ran *before*
`to_representation()` - e.g. via `select_related`/`prefetch_related`
at the queryset level, or a value already cached on the instance from
an earlier access in the same request. This isn't a bug: the profiler
only counts queries that happen *during* that specific field's
rendering step, which correctly shows `0` once a query has been
eliminated (that's the whole point).

## A list response's profile only shows numbers for one row, not aggregated across all of them

Make sure you're reading the profile from the right place -
`ListSerializer.to_representation()` calls `self.child.to_representation()`
per row, so the accumulated profile lives on `serializer.child`, not
on the `ListSerializer` instance itself:

```python
serializer = ArticleSerializer(queryset, many=True)
_ = serializer.data
profile = get_serializer_profile(serializer.child)  # not serializer
```

`ProfileSerializerViewMixin` already handles this correctly for you;
this only matters if you're calling `get_serializer_profile()`
yourself directly. See
[Architecture](architecture.md#why-get_serializer-must-handle-a-listserializers-child-specially).

## `LOG_SLOW_FIELDS` is on but nothing shows up in my logs

Confirm a log handler is actually configured to receive the
`"drf_serializer_performance_profiler"` logger at `WARNING` level or
below - Django's default logging config only shows `WARNING`+ on the
`"django"` logger tree by default; a custom logger needs its own
handler/level configuration (or `propagate = True` up to a root logger
that has one) to actually be visible.

## The header shows a field I didn't expect to see at all

Every field in `Meta.fields` (or explicitly declared) that isn't
`write_only` appears in the profile, including ones you might not
think of as "computed" (a plain `CharField` reading straight off the
model) - this is expected; a fast, 0-query field simply sinks to the
bottom of `slowest_fields()`'s ordering and typically gets truncated
out of the header's default 5-field summary anyway.

## Timing numbers look suspiciously round or zero for a fast field

Sub-millisecond operations can genuinely round to `0.00ms` in the
compact header format (two decimal places) - this isn't a bug, just
display precision. Use `get_serializer_profile()` directly and inspect
`FieldProfile.total_time_ms` (a full-precision `float`) if you need
finer resolution than the header shows.
