"""Custom exceptions raised by :mod:`drf_idempotency`.

All exceptions subclass :class:`rest_framework.exceptions.APIException` so
that, if this package's helpers are used directly inside a DRF view (as
opposed to via the middleware, which handles these itself and converts
them to plain Django responses), raising them produces a sensible HTTP
response automatically.
"""

from __future__ import annotations

from rest_framework.exceptions import APIException


class IdempotencyError(APIException):
    """Base class for all errors raised by this package."""

    default_code = "idempotency_error"


class MissingIdempotencyKeyError(IdempotencyError):
    """Raised when ``REQUIRE_KEY`` is enabled and a request using a
    configured method omits the idempotency key header."""

    status_code = 400
    default_code = "missing_idempotency_key"
    default_detail = "This request requires an Idempotency-Key header."


class InvalidIdempotencyKeyError(IdempotencyError):
    """Raised when a supplied idempotency key fails validation (empty,
    too long, or containing disallowed characters).

    Args:
        reason: A human-readable description of why the key is invalid.
    """

    status_code = 400
    default_code = "invalid_idempotency_key"

    def __init__(self, reason: str) -> None:
        super().__init__(detail=f"Invalid Idempotency-Key: {reason}", code=self.default_code)


class IdempotencyKeyReuseError(IdempotencyError):
    """Raised when an idempotency key is reused with a request whose
    fingerprint (method, path, and body) does not match the original
    request that key was first used for.

    Args:
        key: The reused idempotency key.
    """

    status_code = 422
    default_code = "idempotency_key_reuse"

    def __init__(self, key: str) -> None:
        super().__init__(
            detail=(
                f"The Idempotency-Key {key!r} was previously used with a different "
                f"request. Use a new key for a different request body."
            ),
            code=self.default_code,
        )


class ConcurrentRequestError(IdempotencyError):
    """Raised when another request using the same idempotency key is
    already being processed.

    Args:
        key: The idempotency key currently locked by another request.
    """

    status_code = 409
    default_code = "idempotency_request_in_progress"

    def __init__(self, key: str) -> None:
        super().__init__(
            detail=(
                f"A request with Idempotency-Key {key!r} is already being processed. "
                f"Retry after it completes."
            ),
            code=self.default_code,
        )
