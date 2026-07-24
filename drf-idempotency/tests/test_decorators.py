"""Unit tests for the @idempotent decorator's request-detection helper."""

from __future__ import annotations

import pytest

from drf_idempotency.decorators import _find_request


class TestFindRequest:
    def test_finds_request_as_first_argument(self) -> None:
        class FakeRequest:
            method = "POST"
            headers: dict[str, str] = {}

        req = FakeRequest()
        assert _find_request((req,)) is req

    def test_finds_request_as_second_argument_for_methods(self) -> None:
        class FakeRequest:
            method = "POST"
            headers: dict[str, str] = {}

        class FakeSelf:
            pass

        req = FakeRequest()
        assert _find_request((FakeSelf(), req)) is req

    def test_raises_when_no_request_like_argument_found(self) -> None:
        with pytest.raises(TypeError):
            _find_request((1, 2, 3))

    def test_raises_on_empty_args(self) -> None:
        with pytest.raises(TypeError):
            _find_request(())
