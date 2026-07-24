"""Unit tests for key resolution functions."""

from __future__ import annotations

import pytest

from drf_ratelimit_plus.exceptions import InvalidKeyError
from drf_ratelimit_plus.keys import (
    by_api_key,
    by_ip,
    by_tenant,
    by_user,
    by_view,
    combine,
    resolve_key_func,
)


class _FakeUser:
    def __init__(self, pk: int, is_authenticated: bool = True) -> None:
        self.pk = pk
        self.is_authenticated = is_authenticated


class _FakeRequest:
    def __init__(
        self, *, meta: dict | None = None, headers: dict | None = None, user: object = None
    ) -> None:
        self.META = meta or {}
        self.headers = headers or {}
        self.user = user


class TestByIp:
    def test_uses_remote_addr_by_default(self) -> None:
        request = _FakeRequest(meta={"REMOTE_ADDR": "10.0.0.1"})
        assert by_ip(request) == "10.0.0.1"

    def test_prefers_x_forwarded_for(self) -> None:
        request = _FakeRequest(
            meta={"REMOTE_ADDR": "10.0.0.1", "HTTP_X_FORWARDED_FOR": "203.0.113.5, 10.0.0.1"}
        )
        assert by_ip(request) == "203.0.113.5"

    def test_missing_remote_addr_falls_back_to_unknown(self) -> None:
        request = _FakeRequest()
        assert by_ip(request) == "unknown"


class TestByUser:
    def test_authenticated_user_is_keyed_by_pk(self) -> None:
        request = _FakeRequest(user=_FakeUser(pk=42))
        assert by_user(request) == "user:42"

    def test_anonymous_user_falls_back_to_ip(self) -> None:
        request = _FakeRequest(
            meta={"REMOTE_ADDR": "10.0.0.1"}, user=_FakeUser(pk=0, is_authenticated=False)
        )
        assert by_user(request) == "10.0.0.1"

    def test_no_user_attribute_falls_back_to_ip(self) -> None:
        request = _FakeRequest(meta={"REMOTE_ADDR": "10.0.0.1"})
        assert by_user(request) == "10.0.0.1"


class TestByApiKey:
    def test_uses_configured_header(self) -> None:
        request = _FakeRequest(headers={"X-API-Key": "secret123"})
        assert by_api_key(request) == "apikey:secret123"

    def test_missing_header_falls_back_to_ip(self) -> None:
        request = _FakeRequest(meta={"REMOTE_ADDR": "10.0.0.1"})
        assert by_api_key(request) == "10.0.0.1"


class TestByTenant:
    def test_uses_configured_attribute(self) -> None:
        request = _FakeRequest()
        request.tenant_id = "acme"
        assert by_tenant(request) == "tenant:acme"

    def test_missing_attribute_falls_back_to_ip(self) -> None:
        request = _FakeRequest(meta={"REMOTE_ADDR": "10.0.0.1"})
        assert by_tenant(request) == "10.0.0.1"


class _SampleView:
    pass


class TestByView:
    def test_uses_view_class_path_when_given(self) -> None:
        request = _FakeRequest()
        assert by_view(request, _SampleView()) == f"view:{__name__}._SampleView"

    def test_falls_back_to_path_without_view(self) -> None:
        request = _FakeRequest()
        request.path = "/api/articles/"
        assert by_view(request, None) == "path:/api/articles/"


class TestResolveKeyFunc:
    def test_resolves_builtin_names(self) -> None:
        assert resolve_key_func("ip") is by_ip
        assert resolve_key_func("user") is by_user

    def test_passes_through_callables(self) -> None:
        def custom(request: object, view: object = None) -> str:
            return "x"

        assert resolve_key_func(custom) is custom

    def test_unknown_name_raises(self) -> None:
        with pytest.raises(InvalidKeyError):
            resolve_key_func("bogus")


class TestCombine:
    def test_joins_results_with_pipe(self) -> None:
        request = _FakeRequest(meta={"REMOTE_ADDR": "10.0.0.1"}, user=_FakeUser(pk=42))
        combined = combine("ip", "user")
        assert combined(request) == "10.0.0.1|user:42"

    def test_accepts_callables_too(self) -> None:
        request = _FakeRequest(meta={"REMOTE_ADDR": "10.0.0.1"})
        combined = combine("ip", lambda r, v=None: "custom")
        assert combined(request) == "10.0.0.1|custom"
