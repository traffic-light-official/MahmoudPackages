# Performance

## Overhead per request

`problem_details_exception_handler` only runs on the error path (DRF
calls it exactly once, from `APIView.handle_exception`, after an
exception has already been raised and caught). It performs:

- A handful of `isinstance` checks and, at most, one dict lookup per
  entry in the exception's MRO (`ProblemRegistry._lookup`) - O(depth of
  the exception's class hierarchy), not O(number of registered types).
- One flatten pass over `exc.detail` for validation errors
  (`normalize_validation_error`) - O(number of leaf error messages).
- A `django.utils.translation.override()` context manager, which is a
  cheap thread-local swap.

None of this is on the success-response path, so it has no effect on the
throughput of well-formed requests.

## CorrelationIdMiddleware overhead

Runs on *every* request. Per request it does:

- Two dict lookups (`request.META.get(...)`) and, only on a cache miss
  (no incoming header), a `uuid.uuid4()` call - a fast, non-blocking
  operation with no I/O.
- A cheap string-split-and-length-check for the `traceparent` header.
- Two response header writes.

This is negligible compared to the cost of routing, authentication, and
serialization that already happen on every request; no benchmarking
target is published for this middleware because its cost floor is
several orders of magnitude below normal view/database work.

## Error catalog generation

`build_catalog()` iterates the registry's registered `ErrorType` values
once and sorts them - O(n log n) in the number of *distinct* problem
types your project has registered, typically a few dozen at most, and
is not called on any request path (only from the management command or
tests).

## Recommendations

- Keep `INCLUDE_TIMESTAMP`/`INCLUDE_TRACE_ID`/etc. enabled in
  production; disabling them saves microseconds and is not a
  performance lever worth pulling.
- If you register a very large number of custom exception mappings
  (hundreds), prefer registering base exception classes and letting MRO
  resolution find subclasses, rather than registering every subclass
  individually - this keeps both `ProblemRegistry` dict sizes and
  `all_error_types()` catalog generation time smaller.
