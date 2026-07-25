"""Exceptions raised by :mod:`drf_jwt_auth_kit`."""

from __future__ import annotations


class AuthKitError(Exception):
    """Base class for every exception raised by this package."""


class InvalidTokenError(AuthKitError):
    """Raised when a token is malformed, has a bad signature, or the wrong type."""


class TokenExpiredError(AuthKitError):
    """Raised when a token's ``exp`` claim is in the past."""


class TokenReuseDetectedError(AuthKitError):
    """Raised when an already-rotated (or already-revoked) refresh token is presented again.

    This is the standard signal that a refresh token was stolen: a
    legitimate client always presents the *latest* token in a rotation
    chain, so a repeat of an earlier one means someone else has a copy.
    When raised, every refresh token for the affected device has already
    been revoked.
    """


class DeviceRevokedError(AuthKitError):
    """Raised when a refresh token's device has been revoked (e.g. via logout-all)."""


class MFARequiredError(AuthKitError):
    """Raised during login when the user has MFA enabled but no code was supplied."""


class InvalidMFACodeError(AuthKitError):
    """Raised during login (or MFA enrollment confirmation) when the supplied code is wrong."""


class MFANotEnrolledError(AuthKitError):
    """Raised when confirming or disabling MFA for a user who never started enrollment."""


class InvalidCSRFTokenError(AuthKitError):
    """Raised when a cookie-authenticated request's CSRF token is missing or does not match."""
