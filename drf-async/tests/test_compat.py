"""Tests for :mod:`drf_async.compat`."""

from __future__ import annotations

from drf_async.compat import call_maybe_async, is_async_callable


class TestIsAsyncCallable:
    def test_true_for_a_coroutine_function(self) -> None:
        async def f() -> None:
            pass

        assert is_async_callable(f) is True

    def test_false_for_a_plain_function(self) -> None:
        def f() -> None:
            pass

        assert is_async_callable(f) is False

    def test_false_for_a_bound_sync_method(self) -> None:
        class C:
            def method(self) -> None:
                pass

        assert is_async_callable(C().method) is False

    def test_true_for_a_bound_async_method(self) -> None:
        class C:
            async def method(self) -> None:
                pass

        assert is_async_callable(C().method) is True


class TestCallMaybeAsync:
    async def test_awaits_an_async_function_directly(self) -> None:
        async def f(x: int) -> int:
            return x * 2

        assert await call_maybe_async(f, 3) == 6

    async def test_bridges_a_sync_function_through_a_thread(self) -> None:
        def f(x: int) -> int:
            return x * 2

        assert await call_maybe_async(f, 3) == 6

    async def test_passes_keyword_arguments_through(self) -> None:
        def f(*, x: int, y: int) -> int:
            return x + y

        assert await call_maybe_async(f, x=1, y=2) == 3

    async def test_bound_method_works_too(self) -> None:
        class C:
            def method(self, x: int) -> int:
                return x + 1

        assert await call_maybe_async(C().method, 4) == 5
