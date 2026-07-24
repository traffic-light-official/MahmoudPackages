"""Unit tests for shared request-processing logic."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.test import override_settings
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from drf_idempotency.backends.database import DatabaseBackend
from drf_idempotency.core import applies_to, get_backend, process_idempotent_request, validate_key
from drf_idempotency.exceptions import ConcurrentRequestError, InvalidIdempotencyKeyError
from drf_idempotency.models import IdempotencyRecord

factory = APIRequestFactory()

pytestmark = pytest.mark.django_db


class TestValidateKey:
    def test_valid_key_passes(self) -> None:
        validate_key("abc-123_XYZ.~:")  # must not raise

    def test_empty_key_raises(self) -> None:
        with pytest.raises(InvalidIdempotencyKeyError):
            validate_key("")

    def test_too_long_key_raises(self) -> None:
        with (
            override_settings(IDEMPOTENCY={"MAX_KEY_LENGTH": 5}),
            pytest.raises(InvalidIdempotencyKeyError),
        ):
            validate_key("123456")

    def test_invalid_characters_raise(self) -> None:
        with pytest.raises(InvalidIdempotencyKeyError):
            validate_key("has a space")

    def test_invalid_characters_raise_for_special_chars(self) -> None:
        with pytest.raises(InvalidIdempotencyKeyError):
            validate_key("key/with/slashes")


class TestAppliesTo:
    def test_post_applies_by_default(self) -> None:
        request = factory.post("/x/")
        assert applies_to(request) is True

    def test_get_does_not_apply_by_default(self) -> None:
        request = factory.get("/x/")
        assert applies_to(request) is False

    def test_custom_methods_setting_is_respected(self) -> None:
        with override_settings(IDEMPOTENCY={"METHODS": ["GET"]}):
            assert applies_to(factory.get("/x/")) is True
            assert applies_to(factory.post("/x/")) is False


class TestGetBackend:
    def test_returns_configured_backend_type(self) -> None:
        with override_settings(
            IDEMPOTENCY={"BACKEND": "drf_idempotency.backends.database.DatabaseBackend"}
        ):
            assert isinstance(get_backend(), DatabaseBackend)

    def test_instance_is_cached_across_calls(self) -> None:
        with override_settings(
            IDEMPOTENCY={"BACKEND": "drf_idempotency.backends.database.DatabaseBackend"}
        ):
            assert get_backend() is get_backend()

    def test_changing_setting_invalidates_cache(self) -> None:
        with override_settings(
            IDEMPOTENCY={"BACKEND": "drf_idempotency.backends.database.DatabaseBackend"}
        ):
            first = get_backend()
        with override_settings(
            IDEMPOTENCY={
                "BACKEND": "drf_idempotency.backends.database.DatabaseBackend",
                "BACKEND_OPTIONS": {"foo": "bar"},
            }
        ):
            second = get_backend()
        assert first is not second


class TestProcessIdempotentRequestDirectly:
    """Unit-level tests of the shared dispatch function, bypassing HTTP
    entirely, to exercise paths that are hard to reach through a full
    request cycle (e.g. because Django's own exception-to-response
    conversion intercepts view exceptions before outer middleware sees
    them as raised exceptions - see ``docs/architecture.md``)."""

    def test_exception_from_call_view_releases_the_lock_and_reraises(self) -> None:
        request = Request(
            factory.post("/x/", data={}, format="json", HTTP_IDEMPOTENCY_KEY="unit-key-1")
        )

        def failing_call_view() -> object:
            raise ValueError("boom")

        with pytest.raises(ValueError, match="boom"):
            process_idempotent_request(request, failing_call_view)

        assert not IdempotencyRecord.objects.filter(key="unit-key-1").exists()

    def test_concurrent_in_progress_lock_raises_conflict(self) -> None:
        from drf_idempotency.fingerprint import compute_fingerprint

        request = Request(
            factory.post("/x/", data={}, format="json", HTTP_IDEMPOTENCY_KEY="unit-key-2")
        )

        # Simulate another request already holding the lock, using the
        # same fingerprint this request would compute (otherwise the
        # mismatch check fires first, raising IdempotencyKeyReuseError
        # instead of the concurrency conflict this test targets).
        get_backend().acquire_or_get(
            "unit-key-2", compute_fingerprint(request), lock_ttl=timedelta(seconds=30)
        )

        with pytest.raises(ConcurrentRequestError):
            process_idempotent_request(request, lambda: pytest.fail("call_view must not run"))
