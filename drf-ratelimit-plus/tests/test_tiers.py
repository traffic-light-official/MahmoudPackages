"""Unit tests for plan-tier rate resolution."""

from __future__ import annotations

import pytest
from django.test import override_settings

from drf_ratelimit_plus.exceptions import UnknownTierError
from drf_ratelimit_plus.tiers import default_tier_resolver, resolve_tier_rate


class _FakeUser:
    def __init__(self, plan: str | None) -> None:
        self.plan = plan


class _FakeRequest:
    def __init__(self, user: object = None) -> None:
        self.user = user


class TestDefaultTierResolver:
    def test_reads_user_plan(self) -> None:
        request = _FakeRequest(user=_FakeUser(plan="pro"))
        assert default_tier_resolver(request) == "pro"

    def test_falls_back_to_default_tier_when_no_plan(self) -> None:
        request = _FakeRequest(user=_FakeUser(plan=None))
        assert default_tier_resolver(request) == "default"

    def test_falls_back_to_default_tier_when_no_user(self) -> None:
        request = _FakeRequest()
        assert default_tier_resolver(request) == "default"

    def test_respects_default_tier_setting(self) -> None:
        with override_settings(RATELIMIT_PLUS={"DEFAULT_TIER": "free"}):
            request = _FakeRequest()
            assert default_tier_resolver(request) == "free"


class TestResolveTierRate:
    def test_resolves_matching_tier(self) -> None:
        request = _FakeRequest(user=_FakeUser(plan="pro"))
        tiers = {"free": "10/m", "pro": "100/m"}
        rate = resolve_tier_rate(request, tiers)
        assert rate.count == 100

    def test_falls_back_to_default_tier_entry(self) -> None:
        with override_settings(RATELIMIT_PLUS={"DEFAULT_TIER": "free"}):
            request = _FakeRequest(user=_FakeUser(plan="nonexistent"))
            tiers = {"free": "10/m", "pro": "100/m"}
            rate = resolve_tier_rate(request, tiers)
            assert rate.count == 10

    def test_raises_when_no_matching_tier_and_no_default(self) -> None:
        with override_settings(RATELIMIT_PLUS={"DEFAULT_TIER": "nonexistent"}):
            request = _FakeRequest(user=_FakeUser(plan="also-nonexistent"))
            tiers = {"free": "10/m", "pro": "100/m"}
            with pytest.raises(UnknownTierError):
                resolve_tier_rate(request, tiers)

    def test_custom_resolver(self) -> None:
        request = _FakeRequest()
        tiers = {"a": "1/m", "b": "2/m"}
        rate = resolve_tier_rate(request, tiers, resolver=lambda r: "b")
        assert rate.count == 2
