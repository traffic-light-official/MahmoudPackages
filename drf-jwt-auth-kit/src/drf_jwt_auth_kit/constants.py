"""Shared constants for :mod:`drf_jwt_auth_kit`."""

from __future__ import annotations

from typing import Final

#: JWT ``token_type`` claim value for short-lived access tokens.
TOKEN_TYPE_ACCESS: Final[str] = "access"
#: JWT ``token_type`` claim value for rotating refresh tokens.
TOKEN_TYPE_REFRESH: Final[str] = "refresh"

#: ``Authorization`` header scheme this package expects for access tokens,
#: e.g. ``Authorization: Bearer <token>``.
AUTH_HEADER_PREFIX: Final[str] = "Bearer"

#: Claim name carrying the authenticated user's primary key.
CLAIM_USER_ID: Final[str] = "user_id"
#: Claim name carrying the token type (see ``TOKEN_TYPE_*`` above).
CLAIM_TOKEN_TYPE: Final[str] = "token_type"
#: Claim name carrying the token's unique identifier.
CLAIM_JTI: Final[str] = "jti"
#: Claim name carrying the owning :class:`~drf_jwt_auth_kit.models.Device` primary key.
CLAIM_DEVICE_ID: Final[str] = "device_id"

#: A refresh token was superseded by rotation (the normal, expected path).
REVOKED_REASON_ROTATED: Final[str] = "rotated"
#: A user (or an admin) explicitly logged out this one device.
REVOKED_REASON_LOGOUT: Final[str] = "logout"
#: A user logged out every device at once.
REVOKED_REASON_LOGOUT_ALL: Final[str] = "logout_all"
#: An already-rotated (or already-revoked) refresh token was presented
#: again - the standard signal that a refresh token was stolen and used
#: by an attacker after the legitimate client had already rotated past it.
REVOKED_REASON_REUSE_DETECTED: Final[str] = "reuse_detected"

REVOKED_REASON_CHOICES: Final[tuple[tuple[str, str], ...]] = (
    (REVOKED_REASON_ROTATED, "Rotated"),
    (REVOKED_REASON_LOGOUT, "Logout"),
    (REVOKED_REASON_LOGOUT_ALL, "Logout (all devices)"),
    (REVOKED_REASON_REUSE_DETECTED, "Reuse detected"),
)

#: Login failed because the supplied credentials did not match any user.
LOGIN_FAILURE_INVALID_CREDENTIALS: Final[str] = "invalid_credentials"
#: Login failed because a required MFA code was missing.
LOGIN_FAILURE_MFA_REQUIRED: Final[str] = "mfa_required"
#: Login failed because the supplied MFA code was wrong.
LOGIN_FAILURE_INVALID_MFA_CODE: Final[str] = "invalid_mfa_code"

LOGIN_FAILURE_CHOICES: Final[tuple[tuple[str, str], ...]] = (
    (LOGIN_FAILURE_INVALID_CREDENTIALS, "Invalid credentials"),
    (LOGIN_FAILURE_MFA_REQUIRED, "MFA required"),
    (LOGIN_FAILURE_INVALID_MFA_CODE, "Invalid MFA code"),
)
