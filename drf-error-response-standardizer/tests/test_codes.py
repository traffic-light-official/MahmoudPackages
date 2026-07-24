"""Tests for :mod:`drf_error_response_standardizer.codes`."""

from __future__ import annotations

import dataclasses

import pytest

from drf_error_response_standardizer.codes import BUILTIN_ERROR_TYPES, ErrorType


class TestBuiltinErrorTypes:
    def test_every_entry_key_matches_its_own_code(self) -> None:
        for key, error_type in BUILTIN_ERROR_TYPES.items():
            assert key == error_type.code

    def test_every_slug_is_url_safe_kebab_case(self) -> None:
        for error_type in BUILTIN_ERROR_TYPES.values():
            assert error_type.slug == error_type.slug.lower()
            assert " " not in error_type.slug
            assert "_" not in error_type.slug

    def test_every_status_is_a_valid_http_error_status(self) -> None:
        for error_type in BUILTIN_ERROR_TYPES.values():
            assert 400 <= error_type.status < 600

    def test_validation_error_is_400(self) -> None:
        assert BUILTIN_ERROR_TYPES["validation_error"].status == 400

    def test_server_error_is_500(self) -> None:
        assert BUILTIN_ERROR_TYPES["server_error"].status == 500


class TestErrorType:
    def test_is_frozen(self) -> None:
        error_type = ErrorType(code="x", title="X", slug="x", status=400)

        with pytest.raises(dataclasses.FrozenInstanceError):
            error_type.code = "y"  # type: ignore[misc]
