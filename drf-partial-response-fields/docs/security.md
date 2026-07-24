# Security

## Threat model

`?fields=` is client-controlled input parsed on every request. The
package's security posture follows from that:

1. **Parsing is bounded.** `MAX_FIELDS_LENGTH` (default 2000 characters)
   rejects the raw string before any parsing work happens.
   `MAX_DEPTH` (default 6) bounds recursion depth in the parser, the
   serializer's tree resolution, and the optimizer's nested-`Prefetch`
   construction. Both are configurable — see [Settings](settings.md).
2. **The parser never backtracks or loops on malformed input.** It's a
   single left-to-right pass; malformed input (unbalanced parentheses,
   invalid characters, ambiguous include/exclude mixing) fails fast with
   `InvalidFieldsParameterError` rather than looping or degrading to
   exponential behavior. `tests/test_parser.py::TestPropertyBased` includes
   a `hypothesis`-driven fuzz test and explicit adversarial-input
   regression tests for this.
3. **Unknown field names never error by default.** With `STRICT = False`
   (the default), requesting a field that doesn't exist — including one
   deliberately hidden from a class of users by a permission check — is a
   silent no-op. This avoids using response codes as an oracle for probing
   which field names exist on a serializer. Enable `STRICT = True`
   deliberately, and only for APIs where every possible caller is trusted
   with that information.
4. **Write operations are protected from `fields=` by default.** DRF
   serializers share one field set between input validation and output
   rendering. Without a guard, `?fields=title` on a `POST` would silently
   remove every other writable field from validation, potentially bypassing
   required-field checks. `SAFE_METHODS_ONLY` (default `True`) prevents
   this by ignoring `fields=` entirely on unsafe methods (`POST`, `PUT`,
   `PATCH`, `DELETE`). **Do not disable this** unless you've specifically
   verified your write endpoints don't rely on required-field validation
   that a client could bypass by omission.
5. **Query optimization never changes query results, only query shape.**
   `optimize_queryset()` adds `select_related` / `prefetch_related` /
   `only()` — none of these change which rows are returned or what values
   they contain, only how the same result set is fetched. A permission
   check or queryset filter applied elsewhere in `get_queryset()` is
   unaffected.
6. **No new attack surface for field-level authorization.** This package
   does not implement field-level permissions — if certain fields must be
   hidden from certain users regardless of what they request, that's still
   your application's responsibility (e.g. via a `get_fields()` override
   after this mixin's, as shown in
   [Common Patterns](common-patterns.md#feature-flagged-fields)).
   `?fields=` can only *narrow* what a client sees from the fields the
   serializer would have exposed to them anyway; it never widens access.

## Reporting a vulnerability

See [SECURITY.md](https://github.com/mahmoudgshaker/drf-partial-response-fields/blob/main/SECURITY.md)
in the repository root.

## Recommended production configuration

```python
PARTIAL_RESPONSE_FIELDS = {
    "MAX_DEPTH": 4,             # tighter than the default 6, if your models are shallow
    "MAX_FIELDS_LENGTH": 500,   # tighter than the default 2000, for public APIs
    "STRICT": False,            # keep permissive unless every client is trusted
    "SAFE_METHODS_ONLY": True,  # keep enabled - do not disable without review
}
```

## Dependency security

This package has exactly two runtime dependencies: Django and Django REST
Framework. Keep both current — see [`docs/deployment.md`](deployment.md)
for supported version ranges. Run `pip audit` regularly; there is no
package-specific secret material, credentials, or network I/O anywhere in
this codebase to audit beyond the standard Django/DRF security surface.
