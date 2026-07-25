"""Low-level JWT encoding/decoding.

This module has no database dependency: it only knows how to turn a set
of claims into a signed token and back. Tying a refresh token's ``jti``
to a database row (for rotation and revocation) is
:mod:`drf_jwt_auth_kit.rotation`'s job.
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

import jwt as pyjwt
from django.utils import timezone

from drf_jwt_auth_kit.constants import (
    CLAIM_DEVICE_ID,
    CLAIM_JTI,
    CLAIM_TOKEN_TYPE,
    CLAIM_USER_ID,
    TOKEN_TYPE_ACCESS,
    TOKEN_TYPE_REFRESH,
)
from drf_jwt_auth_kit.exceptions import InvalidTokenError, TokenExpiredError
from drf_jwt_auth_kit.settings import get_setting, get_signing_key, get_verifying_key


def _build_claims(*, lifetime: dt.timedelta, extra: dict[str, Any]) -> dict[str, Any]:
    now = timezone.now()
    claims: dict[str, Any] = {
        "iat": int(now.timestamp()),
        "exp": int((now + lifetime).timestamp()),
    }
    issuer = get_setting("ISSUER")
    if issuer:
        claims["iss"] = issuer
    audience = get_setting("AUDIENCE")
    if audience:
        claims["aud"] = audience
    claims.update(extra)
    return claims


def _encode(claims: dict[str, Any]) -> str:
    return pyjwt.encode(claims, get_signing_key(), algorithm=get_setting("ALGORITHM"))


def encode_access_token(*, user_id: int, device_id: uuid.UUID) -> str:
    """Build and sign a short-lived access token.

    Args:
        user_id: Primary key of the authenticated user.
        device_id: Primary key of the :class:`~drf_jwt_auth_kit.models.Device`
            this token was issued for.

    Returns:
        A signed JWT string.
    """
    claims = _build_claims(
        lifetime=get_setting("ACCESS_TOKEN_LIFETIME"),
        extra={
            CLAIM_USER_ID: user_id,
            CLAIM_TOKEN_TYPE: TOKEN_TYPE_ACCESS,
            CLAIM_DEVICE_ID: str(device_id),
            CLAIM_JTI: str(uuid.uuid4()),
        },
    )
    return _encode(claims)


def encode_refresh_token(
    *, user_id: int, device_id: uuid.UUID, jti: uuid.UUID, lifetime: dt.timedelta
) -> str:
    """Build and sign a refresh token for a specific, pre-created database row.

    Args:
        user_id: Primary key of the authenticated user.
        device_id: Primary key of the owning
            :class:`~drf_jwt_auth_kit.models.Device`.
        jti: Primary key of the
            :class:`~drf_jwt_auth_kit.models.RefreshToken` row this token
            corresponds to - callers are responsible for having already
            created that row before calling this function.
        lifetime: How long this specific token is valid for (normal vs.
            "remember me" refresh tokens have different lifetimes).

    Returns:
        A signed JWT string.
    """
    claims = _build_claims(
        lifetime=lifetime,
        extra={
            CLAIM_USER_ID: user_id,
            CLAIM_TOKEN_TYPE: TOKEN_TYPE_REFRESH,
            CLAIM_DEVICE_ID: str(device_id),
            CLAIM_JTI: str(jti),
        },
    )
    return _encode(claims)


def decode_token(token: str, *, expected_type: str) -> dict[str, Any]:
    """Verify and decode a token's claims.

    Args:
        token: The raw JWT string.
        expected_type: One of the ``TOKEN_TYPE_*`` constants; the
            decoded ``token_type`` claim must match exactly.

    Returns:
        The decoded claims dict.

    Raises:
        TokenExpiredError: If the token's ``exp`` claim is in the past.
        InvalidTokenError: If the signature is invalid, the token is
            malformed, or ``token_type`` does not match ``expected_type``.
    """
    verify_kwargs: dict[str, Any] = {}
    audience = get_setting("AUDIENCE")
    if audience:
        verify_kwargs["audience"] = audience
    issuer = get_setting("ISSUER")
    if issuer:
        verify_kwargs["issuer"] = issuer

    try:
        claims: dict[str, Any] = pyjwt.decode(
            token,
            get_verifying_key(),
            algorithms=[get_setting("ALGORITHM")],
            **verify_kwargs,
        )
    except pyjwt.ExpiredSignatureError as exc:
        raise TokenExpiredError("Token has expired.") from exc
    except pyjwt.PyJWTError as exc:
        raise InvalidTokenError(f"Token is invalid: {exc}") from exc

    actual_type = claims.get(CLAIM_TOKEN_TYPE)
    if actual_type != expected_type:
        raise InvalidTokenError(f"Expected a {expected_type!r} token, got {actual_type!r}.")
    return claims


def token_type_of(token: str) -> str | None:
    """Return the ``token_type`` claim of ``token`` without verifying its signature.

    Used only to give a clearer error message when a token of the wrong
    type is presented; never used for an authorization decision.

    Args:
        token: The raw JWT string.

    Returns:
        The unverified ``token_type`` claim, or ``None`` if the token
        cannot even be decoded as a JWT.
    """
    try:
        unverified: dict[str, Any] = pyjwt.decode(token, options={"verify_signature": False})
    except pyjwt.PyJWTError:
        return None
    value = unverified.get(CLAIM_TOKEN_TYPE)
    return value if isinstance(value, str) else None
