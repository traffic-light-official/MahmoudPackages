# Security

This page covers security considerations specific to
`drf-error-response-standardizer`. For the general vulnerability
reporting process, see [SECURITY.md](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-error-response-standardizer/SECURITY.md).

## Uncaught exceptions never leak internals

For exceptions that are not `APIException` subclasses (a raw
`ValueError`, an unexpected `AttributeError`, a third-party library
error, etc.), the response `detail` is always the fixed
`SERVER_ERROR_DETAIL` setting (default: *"A server error occurred.
Please try again later."*) - never `str(exc)`, a traceback, or any other
representation of the original exception. This is intentional and is
covered by `tests/test_handler.py::TestCatchAll` and
`tests/test_integration.py::TestCatchAllException`: exception messages
frequently contain internal file paths, SQL fragments, or other
implementation details that should never reach an untrusted client.

If you need the real exception for debugging, rely on your existing
error-tracking integration (Sentry, etc.) or Django's own logging of
uncaught exceptions - both still see the original exception, since this
package only affects what is returned to the *client*, not what is
logged internally.

## Correlation/request/trace IDs are not secrets

`CorrelationIdMiddleware` both accepts and echoes these IDs. They are
opaque identifiers with no relationship to authentication or
authorization and are safe to log, forward to third parties, and expose
to end users (e.g. in a support ticket: "please provide this request
ID"). Do not, however, use them as a substitute for a real
authentication/idempotency token - they are not signed, not verified,
and can be set to any string by the caller.

## Validation error `detail` messages

Field-level `errors[].detail` messages come directly from DRF's own
serializer/field validation (the exact same messages DRF's default
handler would have returned) - this package does not add any new
information to what a client could already infer from a standard DRF
error response. If your project has fields with security-sensitive
validation logic (e.g. "this username is already taken" potentially
enabling user enumeration), that consideration exists independently of
this package and should be addressed at the serializer/field level.

## `TYPE_BASE_URI` and the `type` member

The `type` URI is never fetched or dereferenced by this package - it is
purely an identifier, per RFC 9457. If you serve real documentation at
`TYPE_BASE_URI`, ensure that endpoint itself follows your project's
normal access-control and content-security policies; this package has
no opinion on what (if anything) is hosted there.

## Dependency security

- Run `pip audit` regularly against your dependency tree.
- Keep Django and Django REST Framework up to date; this package relies
  on their authentication/permission model and does not re-implement
  any part of it.
- Subscribe to GitHub Security Advisories for this repository to be
  notified of patched releases.
