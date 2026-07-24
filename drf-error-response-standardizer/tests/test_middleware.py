"""Tests for :mod:`drf_error_response_standardizer.middleware`."""

from __future__ import annotations

import uuid

from django.http import HttpRequest, HttpResponse
from rest_framework.test import APIRequestFactory

from drf_error_response_standardizer.constants import (
    CORRELATION_ID_HEADER,
    REQUEST_ID_HEADER,
)
from drf_error_response_standardizer.middleware import (
    CorrelationIdMiddleware,
    get_correlation_id,
    get_request_id,
    get_trace_id,
)


def _make_middleware(captured: dict[str, HttpRequest]) -> CorrelationIdMiddleware:
    def get_response(request: HttpRequest) -> HttpResponse:
        captured["request"] = request
        return HttpResponse()

    return CorrelationIdMiddleware(get_response)


class TestCorrelationId:
    def test_generates_a_uuid_when_no_header_present(self, api_rf: APIRequestFactory) -> None:
        captured: dict[str, HttpRequest] = {}
        middleware = _make_middleware(captured)
        request = api_rf.get("/")

        response = middleware(request)

        correlation_id = get_correlation_id(captured["request"])
        assert correlation_id is not None
        uuid.UUID(correlation_id)  # does not raise
        assert response[CORRELATION_ID_HEADER] == correlation_id

    def test_preserves_incoming_correlation_id_header(self, api_rf: APIRequestFactory) -> None:
        captured: dict[str, HttpRequest] = {}
        middleware = _make_middleware(captured)
        request = api_rf.get("/", HTTP_X_CORRELATION_ID="caller-supplied-id")

        response = middleware(request)

        assert get_correlation_id(captured["request"]) == "caller-supplied-id"
        assert response[CORRELATION_ID_HEADER] == "caller-supplied-id"


class TestRequestId:
    def test_generates_a_uuid_when_no_header_present(self, api_rf: APIRequestFactory) -> None:
        captured: dict[str, HttpRequest] = {}
        middleware = _make_middleware(captured)
        request = api_rf.get("/")

        response = middleware(request)

        request_id = get_request_id(captured["request"])
        assert request_id is not None
        uuid.UUID(request_id)
        assert response[REQUEST_ID_HEADER] == request_id

    def test_preserves_incoming_request_id_header(self, api_rf: APIRequestFactory) -> None:
        captured: dict[str, HttpRequest] = {}
        middleware = _make_middleware(captured)
        request = api_rf.get("/", HTTP_X_REQUEST_ID="caller-request-id")

        middleware(request)

        assert get_request_id(captured["request"]) == "caller-request-id"

    def test_correlation_and_request_ids_are_independent(self, api_rf: APIRequestFactory) -> None:
        captured: dict[str, HttpRequest] = {}
        middleware = _make_middleware(captured)
        request = api_rf.get("/")

        middleware(request)

        assert get_correlation_id(captured["request"]) != get_request_id(captured["request"])


class TestTraceId:
    def test_none_when_no_traceparent_header(self, api_rf: APIRequestFactory) -> None:
        captured: dict[str, HttpRequest] = {}
        middleware = _make_middleware(captured)
        request = api_rf.get("/")

        middleware(request)

        assert get_trace_id(captured["request"]) is None

    def test_extracts_trace_id_from_well_formed_traceparent(
        self, api_rf: APIRequestFactory
    ) -> None:
        captured: dict[str, HttpRequest] = {}
        middleware = _make_middleware(captured)
        request = api_rf.get(
            "/", HTTP_TRACEPARENT="00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
        )

        middleware(request)

        assert get_trace_id(captured["request"]) == "4bf92f3577b34da6a3ce929d0e0e4736"

    def test_none_for_malformed_traceparent(self, api_rf: APIRequestFactory) -> None:
        captured: dict[str, HttpRequest] = {}
        middleware = _make_middleware(captured)
        request = api_rf.get("/", HTTP_TRACEPARENT="not-a-valid-traceparent")

        middleware(request)

        assert get_trace_id(captured["request"]) is None

    def test_none_for_traceparent_with_wrong_trace_id_length(
        self, api_rf: APIRequestFactory
    ) -> None:
        captured: dict[str, HttpRequest] = {}
        middleware = _make_middleware(captured)
        request = api_rf.get("/", HTTP_TRACEPARENT="00-tooshort-00f067aa0ba902b7-01")

        middleware(request)

        assert get_trace_id(captured["request"]) is None


class TestAccessorsWithoutMiddleware:
    def test_accessors_return_none_when_middleware_not_installed(
        self, api_rf: APIRequestFactory
    ) -> None:
        request = api_rf.get("/")

        assert get_correlation_id(request) is None
        assert get_request_id(request) is None
        assert get_trace_id(request) is None
