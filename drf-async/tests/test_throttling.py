"""Tests for :mod:`drf_async.throttling`."""

from __future__ import annotations

import pytest
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory
from rest_framework.throttling import BaseThrottle

from drf_async.throttling import (
    AsyncAnonRateThrottle,
    AsyncSimpleRateThrottle,
    AsyncUserRateThrottle,
    BaseAsyncThrottle,
    check_throttle,
    wait_for_throttle,
)

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    cache.clear()


class _AnonymousUser:
    is_authenticated = False


class _AuthenticatedUser:
    is_authenticated = True
    pk = 42


def _request(user: object = _AnonymousUser()):
    request = RequestFactory().get("/")
    request.user = user
    return request


class TestBaseAsyncThrottleDefaults:
    async def test_allow_request_must_be_overridden(self) -> None:
        throttle = BaseAsyncThrottle()
        with pytest.raises(NotImplementedError):
            await throttle.allow_request(request=object(), view=object())

    async def test_wait_defaults_to_none(self) -> None:
        throttle = BaseAsyncThrottle()
        assert await throttle.wait() is None


class _OnePerMinute(AsyncSimpleRateThrottle):
    scope = "test_scope"
    THROTTLE_RATES = {"test_scope": "1/min"}

    def get_cache_key(self, request: object, view: object) -> str | None:
        return "test-throttle-key"


class TestAsyncSimpleRateThrottle:
    async def test_first_request_is_allowed(self) -> None:
        throttle = _OnePerMinute()
        assert await throttle.allow_request(_request(), view=object()) is True

    async def test_second_request_is_denied(self) -> None:
        first = _OnePerMinute()
        second = _OnePerMinute()
        assert await first.allow_request(_request(), view=object()) is True
        assert await second.allow_request(_request(), view=object()) is False

    async def test_wait_returns_a_positive_number_after_denial(self) -> None:
        throttle = _OnePerMinute()
        await throttle.allow_request(_request(), view=object())
        await throttle.allow_request(_request(), view=object())
        wait = await throttle.wait()
        assert wait is not None
        assert wait > 0

    async def test_prunes_expired_entries_from_history(self) -> None:
        throttle = _OnePerMinute()
        expired_timestamp = throttle.timer() - throttle.duration - 1
        await cache.aset("test-throttle-key", [expired_timestamp], 60)
        assert await throttle.allow_request(_request(), view=object()) is True
        assert expired_timestamp not in throttle.history

    async def test_none_rate_never_throttles(self) -> None:
        class _NoRate(AsyncSimpleRateThrottle):
            scope = "no_rate_scope"
            THROTTLE_RATES = {"no_rate_scope": None}

            def get_cache_key(self, request: object, view: object) -> str | None:
                return "irrelevant"

        throttle = _NoRate()
        assert throttle.rate is None
        assert await throttle.allow_request(_request(), view=object()) is True

    async def test_wait_with_no_history_uses_full_duration(self) -> None:
        throttle = _OnePerMinute()
        wait = await throttle.wait()
        assert wait is not None
        assert wait > 0

    async def test_wait_returns_none_when_over_capacity(self) -> None:
        throttle = _OnePerMinute()
        throttle.history = [throttle.timer(), throttle.timer()]
        assert await throttle.wait() is None

    async def test_none_cache_key_never_throttles(self) -> None:
        class _NoKey(AsyncSimpleRateThrottle):
            scope = "test_scope"
            THROTTLE_RATES = {"test_scope": "1/min"}

            def get_cache_key(self, request: object, view: object) -> str | None:
                return None

        throttle = _NoKey()
        assert await throttle.allow_request(_request(), view=object()) is True
        assert await throttle.allow_request(_request(), view=object()) is True

    def test_preset_rate_skips_get_rate(self) -> None:
        class _PresetRate(AsyncSimpleRateThrottle):
            rate = "3/min"

            def get_cache_key(self, request: object, view: object) -> str | None:
                return "x"

        throttle = _PresetRate()
        assert (throttle.num_requests, throttle.duration) == (3, 60)

    def test_missing_scope_raises_improperly_configured(self) -> None:
        class _NoScope(AsyncSimpleRateThrottle):
            def get_cache_key(self, request: object, view: object) -> str | None:
                return "x"

        with pytest.raises(ImproperlyConfigured, match="must set either"):
            _NoScope()

    def test_unknown_scope_raises_improperly_configured(self) -> None:
        class _UnknownScope(AsyncSimpleRateThrottle):
            scope = "not_a_configured_scope"

            def get_cache_key(self, request: object, view: object) -> str | None:
                return "x"

        with pytest.raises(ImproperlyConfigured, match="No default throttle rate"):
            _UnknownScope()

    def test_get_cache_key_must_be_overridden(self) -> None:
        class _Bare(AsyncSimpleRateThrottle):
            scope = "test_scope"
            THROTTLE_RATES = {"test_scope": "1/min"}

        throttle = _Bare()
        with pytest.raises(NotImplementedError):
            throttle.get_cache_key(_request(), view=object())

    @pytest.mark.parametrize(
        ("rate", "expected"),
        [
            ("1/s", (1, 1)),
            ("5/m", (5, 60)),
            ("10/h", (10, 3600)),
            ("100/d", (100, 86400)),
        ],
    )
    def test_parse_rate(self, rate: str, expected: tuple[int, int]) -> None:
        class _Rated(AsyncSimpleRateThrottle):
            scope = "test_scope"
            THROTTLE_RATES = {"test_scope": rate}

            def get_cache_key(self, request: object, view: object) -> str | None:
                return "x"

        throttle = _Rated()
        assert (throttle.num_requests, throttle.duration) == expected


class TestAsyncAnonRateThrottle:
    def test_returns_none_for_an_authenticated_user(self) -> None:
        throttle = AsyncAnonRateThrottle.__new__(AsyncAnonRateThrottle)
        throttle.rate = "1/min"
        assert throttle.get_cache_key(_request(_AuthenticatedUser()), view=object()) is None

    def test_keys_by_client_ip_for_anonymous(self) -> None:
        throttle = AsyncAnonRateThrottle.__new__(AsyncAnonRateThrottle)
        throttle.rate = "1/min"
        key = throttle.get_cache_key(_request(), view=object())
        assert key is not None
        assert "anon" in key


class TestAsyncUserRateThrottle:
    def test_keys_by_user_pk_when_authenticated(self) -> None:
        throttle = AsyncUserRateThrottle.__new__(AsyncUserRateThrottle)
        throttle.rate = "1/min"
        key = throttle.get_cache_key(_request(_AuthenticatedUser()), view=object())
        assert key is not None
        assert "42" in key

    def test_keys_by_client_ip_when_anonymous(self) -> None:
        throttle = AsyncUserRateThrottle.__new__(AsyncUserRateThrottle)
        throttle.rate = "1/min"
        key = throttle.get_cache_key(_request(), view=object())
        assert key is not None
        assert "user" in key


class _SyncAlwaysThrottle(BaseThrottle):
    def allow_request(self, request: object, view: object) -> bool:
        return False

    def wait(self) -> float:
        return 12.5


class TestCheckThrottleBridging:
    async def test_bridges_a_sync_throttle(self) -> None:
        assert await check_throttle(_SyncAlwaysThrottle(), request=object(), view=object()) is False

    async def test_awaits_an_async_throttle(self) -> None:
        assert await check_throttle(_OnePerMinute(), request=_request(), view=object()) is True


class TestWaitForThrottleBridging:
    async def test_bridges_a_sync_throttle_wait(self) -> None:
        assert await wait_for_throttle(_SyncAlwaysThrottle()) == 12.5

    async def test_awaits_an_async_throttle_wait_of_none(self) -> None:
        assert await wait_for_throttle(BaseAsyncThrottle()) is None
