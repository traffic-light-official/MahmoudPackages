"""Machine-readable error codes and built-in problem type definitions.

Every problem type this package can produce out of the box is declared here
as an :class:`ErrorType`: a stable ``code``, a human title, a relative type
``slug``, and the default HTTP status. The mapping from exception class to
:class:`ErrorType` lives in :mod:`drf_error_response_standardizer.registry`,
which also lets applications register their own exception classes and
:class:`ErrorType` entries.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ErrorType:
    """A named, machine-readable problem type.

    Attributes:
        code: Stable, machine-readable identifier for this error type
            (e.g. ``"validation_error"``, ``"not_authenticated"``). This is
            the value clients should branch on; it never changes once
            published, unlike ``title`` or ``detail``.
        title: Short, human-readable summary (RFC 9457 ``title`` member).
        slug: Relative path segment used to build the RFC 9457 ``type``
            URI when combined with the ``TYPE_BASE_URI`` setting, e.g.
            ``"validation-error"`` -> ``https://api.example.com/problems/validation-error``.
        status: Default HTTP status code for this error type.
    """

    code: str
    title: str
    slug: str
    status: int


#: Built-in error types for Django REST Framework's standard exceptions and
#: for conditions this package itself detects (validation, catch-all 500).
#: Keyed by :attr:`ErrorType.code` for convenient catalog/documentation
#: lookups; :mod:`~drf_error_response_standardizer.registry` indexes these
#: by exception class instead.
BUILTIN_ERROR_TYPES: dict[str, ErrorType] = {
    "validation_error": ErrorType(
        code="validation_error",
        title="Validation Error",
        slug="validation-error",
        status=400,
    ),
    "parse_error": ErrorType(
        code="parse_error",
        title="Malformed Request",
        slug="parse-error",
        status=400,
    ),
    "not_authenticated": ErrorType(
        code="not_authenticated",
        title="Authentication Required",
        slug="not-authenticated",
        status=401,
    ),
    "authentication_failed": ErrorType(
        code="authentication_failed",
        title="Authentication Failed",
        slug="authentication-failed",
        status=401,
    ),
    "permission_denied": ErrorType(
        code="permission_denied",
        title="Permission Denied",
        slug="permission-denied",
        status=403,
    ),
    "not_found": ErrorType(
        code="not_found",
        title="Resource Not Found",
        slug="not-found",
        status=404,
    ),
    "method_not_allowed": ErrorType(
        code="method_not_allowed",
        title="Method Not Allowed",
        slug="method-not-allowed",
        status=405,
    ),
    "not_acceptable": ErrorType(
        code="not_acceptable",
        title="Not Acceptable",
        slug="not-acceptable",
        status=406,
    ),
    "unsupported_media_type": ErrorType(
        code="unsupported_media_type",
        title="Unsupported Media Type",
        slug="unsupported-media-type",
        status=415,
    ),
    "throttled": ErrorType(
        code="throttled",
        title="Request Throttled",
        slug="throttled",
        status=429,
    ),
    "server_error": ErrorType(
        code="server_error",
        title="Internal Server Error",
        slug="server-error",
        status=500,
    ),
}
