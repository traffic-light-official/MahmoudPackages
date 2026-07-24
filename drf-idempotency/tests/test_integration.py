"""End-to-end HTTP tests through the DRF test client and real middleware."""

from __future__ import annotations

import pytest
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APIClient

from tests.test_app.models import Payment

pytestmark = pytest.mark.django_db


@pytest.fixture
def client() -> APIClient:
    return APIClient()


class TestMiddlewareReplay:
    def test_first_request_creates_a_payment(self, client: APIClient) -> None:
        response = client.post(
            "/payments/", {"amount": 100}, format="json", HTTP_IDEMPOTENCY_KEY="key-1"
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Payment.objects.count() == 1

    def test_retry_with_same_key_replays_without_creating_a_second_payment(
        self, client: APIClient
    ) -> None:
        first = client.post(
            "/payments/", {"amount": 100}, format="json", HTTP_IDEMPOTENCY_KEY="key-1"
        )
        second = client.post(
            "/payments/", {"amount": 100}, format="json", HTTP_IDEMPOTENCY_KEY="key-1"
        )
        assert Payment.objects.count() == 1
        assert second.status_code == first.status_code
        assert second.content == first.content

    def test_replayed_response_has_replay_header_true(self, client: APIClient) -> None:
        client.post("/payments/", {"amount": 100}, format="json", HTTP_IDEMPOTENCY_KEY="key-1")
        second = client.post(
            "/payments/", {"amount": 100}, format="json", HTTP_IDEMPOTENCY_KEY="key-1"
        )
        assert second.headers["Idempotent-Replayed"] == "true"

    def test_fresh_response_has_replay_header_false(self, client: APIClient) -> None:
        response = client.post(
            "/payments/", {"amount": 100}, format="json", HTTP_IDEMPOTENCY_KEY="key-1"
        )
        assert response.headers["Idempotent-Replayed"] == "false"

    def test_response_echoes_the_idempotency_key_header(self, client: APIClient) -> None:
        response = client.post(
            "/payments/", {"amount": 100}, format="json", HTTP_IDEMPOTENCY_KEY="key-1"
        )
        assert response.headers["Idempotency-Key"] == "key-1"

    def test_different_keys_both_execute(self, client: APIClient) -> None:
        client.post("/payments/", {"amount": 100}, format="json", HTTP_IDEMPOTENCY_KEY="key-1")
        client.post("/payments/", {"amount": 100}, format="json", HTTP_IDEMPOTENCY_KEY="key-2")
        assert Payment.objects.count() == 2

    def test_no_key_header_processes_normally_every_time(self, client: APIClient) -> None:
        client.post("/payments/", {"amount": 100}, format="json")
        client.post("/payments/", {"amount": 100}, format="json")
        assert Payment.objects.count() == 2

    def test_get_requests_are_unaffected(self, client: APIClient) -> None:
        response = client.get("/payments/", HTTP_IDEMPOTENCY_KEY="key-1")
        # No handler for GET on this view -> 405, but critically the
        # middleware must not have tried to process it as idempotent.
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


class TestKeyReuseDetection:
    def test_same_key_different_body_is_rejected(self, client: APIClient) -> None:
        client.post("/payments/", {"amount": 100}, format="json", HTTP_IDEMPOTENCY_KEY="key-1")
        response = client.post(
            "/payments/", {"amount": 200}, format="json", HTTP_IDEMPOTENCY_KEY="key-1"
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert Payment.objects.count() == 1


class TestInvalidKey:
    def test_invalid_characters_return_400(self, client: APIClient) -> None:
        response = client.post(
            "/payments/", {"amount": 100}, format="json", HTTP_IDEMPOTENCY_KEY="has a space"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestRequireKey:
    def test_missing_key_is_rejected_when_required(self, client: APIClient) -> None:
        with override_settings(
            IDEMPOTENCY={
                "BACKEND": "drf_idempotency.backends.database.DatabaseBackend",
                "REQUIRE_KEY": True,
            }
        ):
            response = client.post("/payments/", {"amount": 100}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_present_key_is_accepted_when_required(self, client: APIClient) -> None:
        with override_settings(
            IDEMPOTENCY={
                "BACKEND": "drf_idempotency.backends.database.DatabaseBackend",
                "REQUIRE_KEY": True,
            }
        ):
            response = client.post(
                "/payments/", {"amount": 100}, format="json", HTTP_IDEMPOTENCY_KEY="key-1"
            )
        assert response.status_code == status.HTTP_201_CREATED


class TestFailureHandling:
    def test_unhandled_exception_releases_the_lock(self, client: APIClient) -> None:
        from drf_idempotency.models import IdempotencyRecord

        with pytest.raises(RuntimeError):
            client.post(
                "/payments-failing/", {"amount": 100}, format="json", HTTP_IDEMPOTENCY_KEY="key-1"
            )
        assert not IdempotencyRecord.objects.filter(key="key-1").exists()

    def test_server_error_response_is_not_cached(self, client: APIClient) -> None:
        first = client.post(
            "/payments-500/", {"amount": 100}, format="json", HTTP_IDEMPOTENCY_KEY="key-1"
        )
        second = client.post(
            "/payments-500/", {"amount": 100}, format="json", HTTP_IDEMPOTENCY_KEY="key-1"
        )
        assert first.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert second.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        # Both executed for real (not a replay) since 5xx isn't cached.
        assert second.headers["Idempotent-Replayed"] == "false"


class TestDecorator:
    def test_decorated_view_replays_like_the_middleware(self, client: APIClient) -> None:
        first = client.post(
            "/payments-decorated/", {"amount": 50}, format="json", HTTP_IDEMPOTENCY_KEY="dkey-1"
        )
        second = client.post(
            "/payments-decorated/", {"amount": 50}, format="json", HTTP_IDEMPOTENCY_KEY="dkey-1"
        )
        assert Payment.objects.count() == 1
        assert second.content == first.content
        assert second.headers["Idempotent-Replayed"] == "true"

    def test_decorated_view_exception_releases_the_lock(self, client: APIClient) -> None:
        from drf_idempotency.models import IdempotencyRecord

        with pytest.raises(RuntimeError):
            client.post(
                "/payments-failing-decorated/",
                {"amount": 100},
                format="json",
                HTTP_IDEMPOTENCY_KEY="dkey-fail",
            )
        assert not IdempotencyRecord.objects.filter(key="dkey-fail").exists()

    def test_decorator_nested_inside_global_middleware_does_not_conflict(
        self, client: APIClient
    ) -> None:
        """The global IdempotencyMiddleware (installed in test settings)
        also wraps this decorated view's request; without the re-entrancy
        guard in ``process_idempotent_request``, this would incorrectly
        raise a 409 Conflict against itself."""
        response = client.post(
            "/payments-decorated/",
            {"amount": 75},
            format="json",
            HTTP_IDEMPOTENCY_KEY="dkey-nested",
        )
        assert response.status_code == status.HTTP_201_CREATED


class TestClientErrorCaching:
    def test_client_error_response_is_cached_by_default(self, client: APIClient) -> None:
        first = client.post("/payments/", {}, format="json", HTTP_IDEMPOTENCY_KEY="bad-key")
        second = client.post("/payments/", {}, format="json", HTTP_IDEMPOTENCY_KEY="bad-key")
        assert first.status_code == status.HTTP_400_BAD_REQUEST
        assert second.headers["Idempotent-Replayed"] == "true"
