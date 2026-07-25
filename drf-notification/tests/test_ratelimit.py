"""Tests for :mod:`drf_notification.ratelimit`."""

from __future__ import annotations

import pytest
from django.test import override_settings

from drf_notification.ratelimit import InvalidRateLimitError, is_rate_limited, parse_rate

# Note: the cache is cleared before every test via the autouse `_clear_cache`
# fixture in conftest.py, so counts in this file are never polluted by
# earlier tests (in this file or any other) touching the same cache keys.


class TestParseRate:
    def test_parses_count_and_period(self) -> None:
        assert parse_rate("50/day") == (50, 86400)
        assert parse_rate("10/hour") == (10, 3600)
        assert parse_rate("1/minute") == (1, 60)
        assert parse_rate("5/second") == (5, 1)

    def test_invalid_format_raises(self) -> None:
        with pytest.raises(InvalidRateLimitError):
            parse_rate("not-a-rate")

    def test_invalid_period_raises(self) -> None:
        with pytest.raises(InvalidRateLimitError, match="period"):
            parse_rate("10/fortnight")

    def test_non_positive_count_raises(self) -> None:
        with pytest.raises(InvalidRateLimitError, match="positive"):
            parse_rate("0/day")

    def test_non_integer_count_raises(self) -> None:
        with pytest.raises(InvalidRateLimitError):
            parse_rate("abc/day")


class TestIsRateLimited:
    def test_no_configured_limit_is_never_limited(self) -> None:
        with override_settings(NOTIFICATIONS={"RATE_LIMITS": {"in_app": None}}):
            for _ in range(100):
                assert is_rate_limited(1, "in_app") is False

    def test_allows_up_to_the_configured_count(self) -> None:
        with override_settings(NOTIFICATIONS={"RATE_LIMITS": {"email": "3/hour"}}):
            assert is_rate_limited(1, "email") is False
            assert is_rate_limited(1, "email") is False
            assert is_rate_limited(1, "email") is False

    def test_blocks_once_the_count_is_exceeded(self) -> None:
        with override_settings(NOTIFICATIONS={"RATE_LIMITS": {"email": "2/hour"}}):
            assert is_rate_limited(1, "email") is False
            assert is_rate_limited(1, "email") is False
            assert is_rate_limited(1, "email") is True

    def test_limits_are_independent_per_user(self) -> None:
        with override_settings(NOTIFICATIONS={"RATE_LIMITS": {"email": "1/hour"}}):
            assert is_rate_limited(1, "email") is False
            assert is_rate_limited(2, "email") is False

    def test_limits_are_independent_per_channel(self) -> None:
        with override_settings(NOTIFICATIONS={"RATE_LIMITS": {"email": "1/hour", "sms": "1/hour"}}):
            assert is_rate_limited(1, "email") is False
            assert is_rate_limited(1, "sms") is False
