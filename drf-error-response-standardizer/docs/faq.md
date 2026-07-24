# FAQ

## Does this replace DRF's `exception_handler` entirely?

Yes - set `REST_FRAMEWORK["EXCEPTION_HANDLER"]` to
`problem_details_exception_handler` and it handles everything DRF's
default handler did (validation, `NotFound`, `PermissionDenied`,
`Throttled`, etc.), plus `Http404`, Django's `PermissionDenied`, custom
exceptions via the registry, and (optionally) any other uncaught
exception. See [Architecture](architecture.md) for exactly how each
exception type is resolved.

## Why does `type` default to `"about:blank"` instead of a real URL?

Per RFC 9457 section 3.1.1, `"about:blank"` means "this problem has no
additional semantics beyond that of the HTTP status code", which is a
perfectly valid, spec-compliant default. Set the `TYPE_BASE_URI` setting
once you have (or plan to have) real documentation pages for your
problem types; every built-in and custom `ErrorType` already carries a
`slug` ready to be combined with it.

## Can I use this without the `errors` array (just a flat `detail`)?

Set `EXPAND_VALIDATION_ERRORS = False` in the
`ERROR_RESPONSE_STANDARDIZER` setting. Validation errors will then be
treated like any other exception: a single, flattened `detail` string
with no `errors` extension member. Most projects want the array left on
- see [Common Patterns](common-patterns.md#frontend-error-handling)
for why it makes frontend integration considerably simpler.

## Migrating from `drf-standardized-errors`

Set `STANDARDIZED_ERRORS_COMPAT = True` in the
`ERROR_RESPONSE_STANDARDIZER` setting. Every error response then
includes a `standardized_errors` extension member with exactly the
shape that package produces (`{"type": ..., "errors": [{"code",
"detail", "attr"}]}`), in addition to the primary RFC 9457 body. This is
meant as a transition aid for clients that have not yet migrated to
reading the RFC 9457 shape - point old client code at
`response.standardized_errors` and new code at the top-level fields,
then remove the setting once every client has migrated. This package
does not aim for byte-for-byte compatibility as a permanent mode; RFC
9457 compliance is the primary, supported shape.

## Does this affect performance?

No measurably - see [Performance](performance.md). The exception
handler only runs on the error path, and `CorrelationIdMiddleware`'s
per-request cost is dominated by a UUID generation on cache miss, which
is negligible next to routing/auth/serialization.

## Can I have different problem types per API version?

Yes - build a separate `ProblemRegistry` per version and bind it via
`functools.partial`. See
[Common Patterns](common-patterns.md#scoping-a-registry-per-api-version).

## Does the `errors` array work with `many=True` serializers?

Yes. Per-item validation errors on a `many=True` `ListSerializer` are
flattened with an index in the pointer, e.g. `"1/title"` for the second
item's `title` field. See `normalize_validation_error` in
[API Reference](api-reference.md#normalize_validation_error).

## Why is there no `WWW-Authenticate` header on my 401 response?

DRF only sets `exc.auth_header` when at least one configured
authentication class implements `authenticate_header()` (e.g.
`BasicAuthentication`, `TokenAuthentication`) - this package preserves
whatever DRF already attached, it does not invent the header itself. If
your view uses only `SessionAuthentication` (which does not implement
`authenticate_header()`), DRF raises `PermissionDenied` (403) instead of
`NotAuthenticated` (401) for anonymous requests, and no
`WWW-Authenticate` header is expected in that case either - this is
standard DRF behavior, unrelated to this package.
