# Settings

All configuration lives under a single Django setting, `PARTIAL_RESPONSE_FIELDS`,
a dict of overrides merged on top of the defaults below. Settings are
validated eagerly (on first access) and the validated result is cached —
the cache is automatically invalidated by Django's `setting_changed`
signal, so `@override_settings(PARTIAL_RESPONSE_FIELDS={...})` works
correctly in tests.

```python
# settings.py
PARTIAL_RESPONSE_FIELDS = {
    "QUERY_PARAM": "fields",
    "STRICT": True,
    "MAX_DEPTH": 4,
}
```

Any key not listed below raises `django.core.exceptions.ImproperlyConfigured`
the first time a setting is read — this catches typos in your settings
file immediately rather than silently ignoring them.

## QUERY_PARAM

- **Type:** `str`
- **Default:** `"fields"`

The query parameter name clients use to request a subset of fields, e.g.
`?fields=id,name`. Must be a valid Python identifier.

## MAX_DEPTH

- **Type:** `int`
- **Default:** `6`

Maximum allowed nesting depth of the `fields` expression. For example,
`a(b(c(d)))` has depth 4. Requests exceeding this raise
`InvalidFieldsParameterError` (HTTP 400) rather than recursing arbitrarily
deep — this is a deliberate guard against pathological input.

## MAX_FIELDS_LENGTH

- **Type:** `int`
- **Default:** `2000`

Maximum accepted length, in characters, of the raw `fields` query
parameter value. Requests exceeding this are rejected before any parsing
work is attempted.

## STRICT

- **Type:** `bool`
- **Default:** `False`

When `True`, requesting a field name that doesn't exist on the serializer
raises `UnknownFieldError` (HTTP 400). When `False` (the default), unknown
names are silently dropped from the response. See
[Configuration](configuration.md#deciding-on-strict-mode) for the tradeoffs.

## ALWAYS_INCLUDE

- **Type:** `list[str]` or `tuple[str, ...]`
- **Default:** `["id"]`

Field names that are always present in the response regardless of what was
requested. The primary key is included by default because pagination,
hyperlinking, and client-side caching typically depend on it.

## ENABLE_QUERY_OPTIMIZATION

- **Type:** `bool`
- **Default:** `True`

When `False`, disables the automatic `select_related` / `prefetch_related`
/ `only()` optimization performed by `PartialResponseMixin.get_queryset()`.
Field filtering on the serializer is unaffected — only the queryset
optimization step is skipped. Useful for isolating whether a performance
issue is caused by the optimizer or by something else.

## SAFE_METHODS_ONLY

- **Type:** `bool`
- **Default:** `True`

When `True` (the default), `PartialResponseMixin` only honors the `fields`
parameter on safe HTTP methods (`GET`, `HEAD`, `OPTIONS`); unsafe methods
(`POST`, `PUT`, `PATCH`, `DELETE`) always see the full, unfiltered field
set for both input validation and output rendering.

This matters because DRF serializers share one field set between input
validation and output rendering: without this guard, `?fields=title` on a
`POST` would make every other writable field vanish from validation too,
silently disabling required-field checks. See [Security](security.md) for
the full explanation. Only disable this if you've verified your write
endpoints don't depend on fields being present that a client might omit
via `fields=`.

## Settings validation errors

Every misconfiguration raises `django.core.exceptions.ImproperlyConfigured`
with a message naming the offending key and what was expected:

```pycon
>>> from django.test import override_settings
>>> with override_settings(PARTIAL_RESPONSE_FIELDS={"MAX_DEPTH": 0}):
...     get_setting("MAX_DEPTH")
...
django.core.exceptions.ImproperlyConfigured: 'PARTIAL_RESPONSE_FIELDS["MAX_DEPTH"]' must be at least 1.
```
