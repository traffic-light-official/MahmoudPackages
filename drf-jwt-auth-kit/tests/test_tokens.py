"""Tests for :mod:`drf_jwt_auth_kit.tokens`."""

from __future__ import annotations

import datetime as dt
import uuid

import jwt as pyjwt
import pytest
from django.test import override_settings
from freezegun import freeze_time

from drf_jwt_auth_kit.constants import CLAIM_DEVICE_ID, CLAIM_JTI, CLAIM_TOKEN_TYPE, CLAIM_USER_ID
from drf_jwt_auth_kit.exceptions import InvalidTokenError, TokenExpiredError
from drf_jwt_auth_kit.tokens import (
    decode_token,
    encode_access_token,
    encode_refresh_token,
    token_type_of,
)


class TestEncodeAccessToken:
    def test_round_trips_claims(self) -> None:
        device_id = uuid.uuid4()
        token = encode_access_token(user_id=42, device_id=device_id)

        claims = decode_token(token, expected_type="access")

        assert claims[CLAIM_USER_ID] == 42
        assert claims[CLAIM_DEVICE_ID] == str(device_id)
        assert claims[CLAIM_TOKEN_TYPE] == "access"

    def test_each_call_gets_a_unique_jti(self) -> None:
        device_id = uuid.uuid4()
        first = decode_token(
            encode_access_token(user_id=1, device_id=device_id), expected_type="access"
        )
        second = decode_token(
            encode_access_token(user_id=1, device_id=device_id), expected_type="access"
        )

        assert first[CLAIM_JTI] != second[CLAIM_JTI]

    def test_expires_after_configured_lifetime(self) -> None:
        device_id = uuid.uuid4()
        with freeze_time("2026-01-01T00:00:00Z"):
            token = encode_access_token(user_id=1, device_id=device_id)

        with freeze_time("2026-01-01T00:04:00Z"):
            decode_token(token, expected_type="access")  # still valid

        with freeze_time("2026-01-01T00:06:00Z"), pytest.raises(TokenExpiredError):
            decode_token(token, expected_type="access")


class TestEncodeRefreshToken:
    def test_round_trips_claims(self) -> None:
        device_id = uuid.uuid4()
        jti = uuid.uuid4()
        token = encode_refresh_token(
            user_id=7, device_id=device_id, jti=jti, lifetime=dt.timedelta(days=7)
        )

        claims = decode_token(token, expected_type="refresh")

        assert claims[CLAIM_USER_ID] == 7
        assert claims[CLAIM_JTI] == str(jti)
        assert claims[CLAIM_DEVICE_ID] == str(device_id)


class TestDecodeToken:
    def test_rejects_wrong_token_type(self) -> None:
        token = encode_access_token(user_id=1, device_id=uuid.uuid4())

        with pytest.raises(InvalidTokenError, match="Expected a 'refresh' token"):
            decode_token(token, expected_type="refresh")

    def test_rejects_malformed_token(self) -> None:
        with pytest.raises(InvalidTokenError):
            decode_token("not-a-real-token", expected_type="access")

    def test_rejects_tampered_signature(self) -> None:
        token = encode_access_token(user_id=1, device_id=uuid.uuid4())
        tampered = token[:-1] + ("a" if token[-1] != "a" else "b")

        with pytest.raises(InvalidTokenError):
            decode_token(tampered, expected_type="access")

    def test_rejects_token_signed_with_a_different_key(self) -> None:
        claims = {"user_id": 1, "token_type": "access", "exp": 9999999999}
        token = pyjwt.encode(
            claims, "a-completely-different-key-that-is-long-enough", algorithm="HS256"
        )

        with pytest.raises(InvalidTokenError):
            decode_token(token, expected_type="access")

    def test_includes_issuer_and_audience_when_configured(self) -> None:
        with override_settings(JWT_AUTH_KIT={"ISSUER": "my-app", "AUDIENCE": "my-api"}):
            token = encode_access_token(user_id=1, device_id=uuid.uuid4())
            claims = decode_token(token, expected_type="access")

        assert claims["iss"] == "my-app"
        assert claims["aud"] == "my-api"

    def test_wrong_audience_is_rejected(self) -> None:
        with override_settings(JWT_AUTH_KIT={"AUDIENCE": "my-api"}):
            token = encode_access_token(user_id=1, device_id=uuid.uuid4())

        with (
            override_settings(JWT_AUTH_KIT={"AUDIENCE": "a-different-api"}),
            pytest.raises(InvalidTokenError),
        ):
            decode_token(token, expected_type="access")


class TestTokenTypeOf:
    def test_returns_the_unverified_token_type(self) -> None:
        token = encode_access_token(user_id=1, device_id=uuid.uuid4())

        assert token_type_of(token) == "access"

    def test_returns_none_for_garbage_input(self) -> None:
        assert token_type_of("not-a-jwt-at-all") is None

    def test_works_even_with_a_tampered_signature(self) -> None:
        token = encode_access_token(user_id=1, device_id=uuid.uuid4())
        tampered = token[:-1] + ("a" if token[-1] != "a" else "b")

        assert token_type_of(tampered) == "access"
