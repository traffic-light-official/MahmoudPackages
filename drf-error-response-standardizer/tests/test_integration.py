"""End-to-end tests exercising the full middleware + exception handler stack.

These tests hit real URLs through ``rest_framework.test.APIClient`` (which
routes through the actual Django middleware stack and DRF's
``APIView.handle_exception``), rather than calling
:func:`~drf_error_response_standardizer.handler.problem_details_exception_handler`
directly, to verify the pieces are wired together correctly end-to-end:
``CorrelationIdMiddleware`` header propagation, DRF's own header injection
(``WWW-Authenticate``, ``Retry-After``) before the handler runs, and nested
serializer validation error normalization through a real ``ModelSerializer``.
"""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from tests.test_app.models import Author

pytestmark = pytest.mark.django_db


class TestCorrelationIdPropagation:
    def test_correlation_id_is_echoed_on_success_responses(self, api_client: APIClient) -> None:
        response = api_client.get("/articles/")

        assert "X-Correlation-ID" in response.headers
        assert "X-Request-ID" in response.headers

    def test_incoming_correlation_id_is_preserved(self, api_client: APIClient) -> None:
        response = api_client.get("/articles/", HTTP_X_CORRELATION_ID="caller-id-123")

        assert response.headers["X-Correlation-ID"] == "caller-id-123"

    def test_correlation_id_is_included_on_error_responses(self, api_client: APIClient) -> None:
        response = api_client.get("/raise-404/", HTTP_X_CORRELATION_ID="caller-id-456")

        assert response.status_code == 404
        assert response.data["correlation_id"] == "caller-id-456"
        assert response.headers["X-Correlation-ID"] == "caller-id-456"


class TestNestedValidationErrors:
    def test_invalid_nested_author_email_is_reported_with_slash_pointer(
        self, api_client: APIClient
    ) -> None:
        response = api_client.post(
            "/articles/",
            {
                "title": "New Post",
                "body": "Body text.",
                "author": {"name": "Bob", "email": "not-an-email"},
            },
            format="json",
        )

        assert response.status_code == 400
        assert response["Content-Type"].startswith("application/problem+json")
        pointers = {entry["pointer"] for entry in response.data["errors"]}
        assert "author/email" in pointers

    def test_missing_required_top_level_field(self, api_client: APIClient) -> None:
        response = api_client.post("/articles/", {"body": "Body text."}, format="json")

        assert response.status_code == 400
        pointers = {entry["pointer"] for entry in response.data["errors"]}
        assert "title" in pointers
        assert "author" in pointers

    def test_valid_payload_creates_the_article(self, api_client: APIClient) -> None:
        response = api_client.post(
            "/articles/",
            {
                "title": "New Post",
                "body": "Body text.",
                "author": {"name": "Bob", "email": "bob@example.com"},
            },
            format="json",
        )

        assert response.status_code == 201


class TestConflictError:
    def test_conflict_error_returns_409_with_extensions(self, api_client: APIClient) -> None:
        response = api_client.get("/raise-conflict/")

        assert response.status_code == 409
        assert response.data["title"] == "Conflict"
        assert response.data["detail"] == "Order has already shipped."
        assert response.data["order_id"] == 42


class TestHttp404:
    def test_django_http404_is_standardized(self, api_client: APIClient) -> None:
        response = api_client.get("/raise-404/")

        assert response.status_code == 404
        assert response.data["detail"] == "Widget not found."
        assert response.data["code"] == "not_found"


class TestAuthentication:
    def test_unauthenticated_request_returns_401_with_www_authenticate(
        self, api_client: APIClient
    ) -> None:
        response = api_client.get("/requires-auth/")

        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers
        assert response.data["code"] == "not_authenticated"


class TestThrottling:
    def test_second_request_is_throttled_with_retry_after(self, api_client: APIClient) -> None:
        first = api_client.get("/throttled/")
        assert first.status_code == 200

        second = api_client.get("/throttled/")

        assert second.status_code == 429
        assert "Retry-After" in second.headers
        assert second.data["code"] == "throttled"


class TestCatchAllException:
    def test_unhandled_value_error_becomes_generic_500(self, api_client: APIClient) -> None:
        response = api_client.get("/raise-value-error/")

        assert response.status_code == 500
        assert response.data["code"] == "server_error"
        assert "Something went wrong internally." not in response.data["detail"]


class TestArticleViewSetNotFound:
    def test_retrieving_missing_article_returns_standardized_404(
        self, api_client: APIClient, author: Author
    ) -> None:
        response = api_client.get("/articles/999999/")

        assert response.status_code == 404
        assert response.data["type"] == "about:blank"
        assert response.data["code"] == "not_found"
