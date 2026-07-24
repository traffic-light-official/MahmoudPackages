"""Unit tests for rate string parsing."""

from __future__ import annotations

import pytest

from drf_ratelimit_plus.exceptions import InvalidRateError
from drf_ratelimit_plus.rates import Rate, parse_rate


class TestParseRate:
    @pytest.mark.parametrize(
        ("raw", "count", "period"),
        [
            ("100/m", 100, 60),
            ("1000/h", 1000, 3600),
            ("10/s", 10, 1),
            ("5/d", 5, 86400),
            ("100/minute", 100, 60),
            ("100/hour", 100, 3600),
            ("100/second", 100, 1),
            ("100/day", 100, 86400),
            ("100/min", 100, 60),
            ("100/sec", 100, 1),
        ],
    )
    def test_valid_rates(self, raw: str, count: int, period: int) -> None:
        rate = parse_rate(raw)
        assert rate.count == count
        assert rate.period == period

    def test_whitespace_is_tolerated(self) -> None:
        rate = parse_rate(" 100 / m ")
        assert rate.count == 100
        assert rate.period == 60

    def test_case_insensitive_period(self) -> None:
        assert parse_rate("100/M").period == 60
        assert parse_rate("100/Hour").period == 3600

    def test_already_parsed_rate_passes_through(self) -> None:
        original = Rate(count=42, period=10)
        assert parse_rate(original) is original

    def test_per_second_property(self) -> None:
        assert parse_rate("60/m").per_second == 1.0
        assert parse_rate("10/s").per_second == 10.0

    def test_invalid_format_raises(self) -> None:
        with pytest.raises(InvalidRateError):
            parse_rate("not-a-rate")

    def test_missing_slash_raises(self) -> None:
        with pytest.raises(InvalidRateError):
            parse_rate("100m")

    def test_unknown_period_raises(self) -> None:
        with pytest.raises(InvalidRateError):
            parse_rate("100/fortnight")

    def test_zero_count_raises(self) -> None:
        with pytest.raises(InvalidRateError):
            parse_rate("0/m")

    def test_negative_count_raises(self) -> None:
        with pytest.raises(InvalidRateError):
            parse_rate("-5/m")

    def test_non_integer_count_raises(self) -> None:
        with pytest.raises(InvalidRateError):
            parse_rate("1.5/m")
