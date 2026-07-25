"""Tests for :mod:`drf_notification.unsubscribe`."""

from __future__ import annotations

import time

import pytest
from django.test import override_settings

from drf_notification.exceptions import InvalidUnsubscribeTokenError
from drf_notification.unsubscribe import generate_unsubscribe_token, resolve_unsubscribe_token


class TestGenerateAndResolve:
    def test_round_trips_a_specific_event(self) -> None:
        token = generate_unsubscribe_token(42, "order.shipped")

        user_id, event_key = resolve_unsubscribe_token(token)

        assert user_id == 42
        assert event_key == "order.shipped"

    def test_round_trips_unsubscribe_from_everything(self) -> None:
        token = generate_unsubscribe_token(42, None)

        user_id, event_key = resolve_unsubscribe_token(token)

        assert user_id == 42
        assert event_key is None

    def test_tokens_for_different_users_differ(self) -> None:
        assert generate_unsubscribe_token(1, "e") != generate_unsubscribe_token(2, "e")

    def test_tampered_token_is_rejected(self) -> None:
        token = generate_unsubscribe_token(42, "order.shipped")
        tampered = token[:-1] + ("a" if token[-1] != "a" else "b")

        with pytest.raises(InvalidUnsubscribeTokenError):
            resolve_unsubscribe_token(tampered)

    def test_malformed_token_is_rejected(self) -> None:
        with pytest.raises(InvalidUnsubscribeTokenError):
            resolve_unsubscribe_token("not-a-real-token")

    def test_expired_token_is_rejected(self) -> None:
        with override_settings(NOTIFICATIONS={"UNSUBSCRIBE_TOKEN_MAX_AGE": 1}):
            token = generate_unsubscribe_token(42, "order.shipped")
            time.sleep(1.1)
            with pytest.raises(InvalidUnsubscribeTokenError, match="expired"):
                resolve_unsubscribe_token(token)
