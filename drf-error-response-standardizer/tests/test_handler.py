"""Tests for :mod:`drf_error_response_standardizer.handler`."""

from __future__ import annotations

from typing import Any

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404, HttpRequest
from django.test import override_settings
from rest_framework import exceptions as drf_exceptions
from rest_framework.test import APIRequestFactory

from drf_error_response_standardizer.codes import ErrorType
from drf_error_response_standardizer.exceptions import ConflictError, ProblemAPIException
from drf_error_response_standardizer.handler import problem_details_exception_handler
from drf_error_response_standardizer.problem import ProblemDetail
from drf_error_response_standardizer.registry import ProblemRegistry


def _context(request: HttpRequest | None) -> dict[str, Any]:
    return {"request": request, "view": None, "args": (), "kwargs": {}}


class TestProblemApiException:
    def test_builds_response_from_exception_attributes(self, api_rf: APIRequestFactory) -> None:
        exc = ConflictError("Order already shipped.", extensions={"order_id": 42})

        response = problem_details_exception_handler(exc, _context(api_rf.get("/orders/1/")))

        assert response is not None
        assert response.status_code == 409
        assert response.data["title"] == "Conflict"
        assert response.data["detail"] == "Order already shipped."
        assert response.data["code"] == "conflict"
        assert response.data["order_id"] == 42

    def test_about_blank_type_when_no_slug_set(self, api_rf: APIRequestFactory) -> None:
        exc = ProblemAPIException("Something.", status_code=400)

        response = problem_details_exception_handler(exc, _context(api_rf.get("/")))

        assert response is not None
        assert response.data["type"] == "about:blank"

    def test_nested_dict_and_list_detail_resolves_first_code(
        self, api_rf: APIRequestFactory
    ) -> None:
        exc = ProblemAPIException(
            detail={"a": ["first message", "second message"]}, code="nested_code"
        )

        response = problem_details_exception_handler(exc, _context(api_rf.get("/")))

        assert response is not None
        assert response.data["code"] == "nested_code"


class TestCustomBuilder:
    def test_registered_builder_takes_precedence(self, api_rf: APIRequestFactory) -> None:
        class DomainError(Exception):
            pass

        registry = ProblemRegistry()
        registry.register_builder(
            DomainError, lambda exc: ProblemDetail(status=418, title="I'm a teapot")
        )

        response = problem_details_exception_handler(
            DomainError(), _context(api_rf.get("/")), registry=registry
        )

        assert response is not None
        assert response.status_code == 418
        assert response.data["title"] == "I'm a teapot"


class TestValidationError:
    def test_single_non_field_message_collapses_to_plain_detail(
        self, api_rf: APIRequestFactory
    ) -> None:
        exc = drf_exceptions.ValidationError("Cannot process this request.")

        response = problem_details_exception_handler(exc, _context(api_rf.get("/")))

        assert response is not None
        assert response.status_code == 400
        assert response.data["detail"] == "Cannot process this request."
        assert "errors" not in response.data

    def test_field_errors_are_expanded_into_errors_array(self, api_rf: APIRequestFactory) -> None:
        exc = drf_exceptions.ValidationError(
            {
                "title": [drf_exceptions.ErrorDetail("This field is required.", code="required")],
                "author": {
                    "email": [drf_exceptions.ErrorDetail("Enter a valid email.", code="invalid")]
                },
            }
        )

        response = problem_details_exception_handler(exc, _context(api_rf.get("/")))

        assert response is not None
        assert response.status_code == 400
        assert response.data["code"] == "validation_error"
        pointers = {entry["pointer"] for entry in response.data["errors"]}
        assert pointers == {"title", "author/email"}

    def test_empty_detail_produces_generic_detail_with_no_errors_array(
        self, api_rf: APIRequestFactory
    ) -> None:
        exc = drf_exceptions.ValidationError({})

        response = problem_details_exception_handler(exc, _context(api_rf.get("/")))

        assert response is not None
        assert response.data["detail"] == "One or more fields failed validation."
        assert "errors" not in response.data

    def test_expand_validation_errors_false_falls_back_to_generic_api_exception(
        self, api_rf: APIRequestFactory
    ) -> None:
        exc = drf_exceptions.ValidationError({"title": ["Required."]})

        with override_settings(ERROR_RESPONSE_STANDARDIZER={"EXPAND_VALIDATION_ERRORS": False}):
            response = problem_details_exception_handler(exc, _context(api_rf.get("/")))

        assert response is not None
        assert "errors" not in response.data


class TestGenericApiException:
    def test_unregistered_api_exception_uses_humanized_title_and_own_status(
        self, api_rf: APIRequestFactory
    ) -> None:
        class CustomException(drf_exceptions.APIException):
            status_code = 451
            default_detail = "Unavailable for legal reasons."
            default_code = "legal_block"

        response = problem_details_exception_handler(CustomException(), _context(api_rf.get("/")))

        assert response is not None
        assert response.status_code == 451
        assert response.data["title"] == "Custom Exception"
        assert response.data["code"] == "legal_block"
        assert response.data["detail"] == "Unavailable for legal reasons."

    def test_registered_api_exception_uses_registered_error_type(
        self, api_rf: APIRequestFactory
    ) -> None:
        response = problem_details_exception_handler(
            drf_exceptions.NotFound(), _context(api_rf.get("/missing/"))
        )

        assert response is not None
        assert response.status_code == 404
        assert response.data["code"] == "not_found"
        assert response.data["title"] == "Resource Not Found"


class TestNonApiExceptionRegistryFallback:
    def test_http404_is_mapped_via_registry(self, api_rf: APIRequestFactory) -> None:
        response = problem_details_exception_handler(
            Http404("Widget not found."), _context(api_rf.get("/widgets/1/"))
        )

        assert response is not None
        assert response.status_code == 404
        assert response.data["detail"] == "Widget not found."

    def test_django_permission_denied_is_mapped_via_registry(
        self, api_rf: APIRequestFactory
    ) -> None:
        response = problem_details_exception_handler(
            DjangoPermissionDenied("Nope."), _context(api_rf.get("/"))
        )

        assert response is not None
        assert response.status_code == 403


class TestCatchAll:
    def test_unhandled_exception_becomes_generic_500(self, api_rf: APIRequestFactory) -> None:
        response = problem_details_exception_handler(ValueError("boom"), _context(api_rf.get("/")))

        assert response is not None
        assert response.status_code == 500
        assert response.data["code"] == "server_error"
        assert response.data["detail"] == "A server error occurred. Please try again later."
        assert "boom" not in response.data["detail"]

    def test_catch_all_disabled_returns_none(self, api_rf: APIRequestFactory) -> None:
        with override_settings(ERROR_RESPONSE_STANDARDIZER={"CATCH_ALL_EXCEPTIONS": False}):
            response = problem_details_exception_handler(
                ValueError("boom"), _context(api_rf.get("/"))
            )

        assert response is None


class TestHeaders:
    def test_www_authenticate_header_is_preserved(self, api_rf: APIRequestFactory) -> None:
        exc = drf_exceptions.NotAuthenticated()
        exc.auth_header = 'Basic realm="api"'

        response = problem_details_exception_handler(exc, _context(api_rf.get("/")))

        assert response is not None
        assert response["WWW-Authenticate"] == 'Basic realm="api"'

    def test_retry_after_header_is_preserved(self, api_rf: APIRequestFactory) -> None:
        exc = drf_exceptions.Throttled(wait=12)

        response = problem_details_exception_handler(exc, _context(api_rf.get("/")))

        assert response is not None
        assert response["Retry-After"] == "12"


class TestMediaType:
    def test_default_content_type_is_problem_json(self, api_rf: APIRequestFactory) -> None:
        response = problem_details_exception_handler(
            drf_exceptions.NotFound(), _context(api_rf.get("/"))
        )

        assert response is not None
        assert response.content_type == "application/problem+json"

    def test_media_type_setting_can_be_overridden(self, api_rf: APIRequestFactory) -> None:
        with override_settings(ERROR_RESPONSE_STANDARDIZER={"MEDIA_TYPE": "application/json"}):
            response = problem_details_exception_handler(
                drf_exceptions.NotFound(), _context(api_rf.get("/"))
            )

        assert response is not None
        assert response.content_type == "application/json"


class TestExtensionToggles:
    def test_instance_defaults_to_request_path(self, api_rf: APIRequestFactory) -> None:
        response = problem_details_exception_handler(
            drf_exceptions.NotFound(), _context(api_rf.get("/widgets/1/"))
        )

        assert response is not None
        assert response.data["instance"] == "/widgets/1/"

    def test_instance_omitted_when_disabled(self, api_rf: APIRequestFactory) -> None:
        with override_settings(ERROR_RESPONSE_STANDARDIZER={"INCLUDE_INSTANCE": False}):
            response = problem_details_exception_handler(
                drf_exceptions.NotFound(), _context(api_rf.get("/widgets/1/"))
            )

        assert response is not None
        assert "instance" not in response.data

    def test_timestamp_present_by_default_and_is_iso_formatted(
        self, api_rf: APIRequestFactory
    ) -> None:
        import datetime as dt

        response = problem_details_exception_handler(
            drf_exceptions.NotFound(), _context(api_rf.get("/"))
        )

        assert response is not None
        dt.datetime.fromisoformat(response.data["timestamp"])

    def test_timestamp_omitted_when_disabled(self, api_rf: APIRequestFactory) -> None:
        with override_settings(ERROR_RESPONSE_STANDARDIZER={"INCLUDE_TIMESTAMP": False}):
            response = problem_details_exception_handler(
                drf_exceptions.NotFound(), _context(api_rf.get("/"))
            )

        assert response is not None
        assert "timestamp" not in response.data

    def test_no_request_in_context_still_produces_a_response(self) -> None:
        response = problem_details_exception_handler(drf_exceptions.NotFound(), _context(None))

        assert response is not None
        assert "instance" not in response.data


class TestTypeBaseUri:
    def test_builds_full_type_uri_when_configured(self, api_rf: APIRequestFactory) -> None:
        with override_settings(
            ERROR_RESPONSE_STANDARDIZER={"TYPE_BASE_URI": "https://api.example.com/problems/"}
        ):
            response = problem_details_exception_handler(
                drf_exceptions.NotFound(), _context(api_rf.get("/"))
            )

        assert response is not None
        assert response.data["type"] == "https://api.example.com/problems/not-found"


class TestStandardizedErrorsCompat:
    def test_adds_standardized_errors_extension_for_validation_error(
        self, api_rf: APIRequestFactory
    ) -> None:
        exc = drf_exceptions.ValidationError(
            {"title": [drf_exceptions.ErrorDetail("Required.", code="required")]}
        )

        with override_settings(ERROR_RESPONSE_STANDARDIZER={"STANDARDIZED_ERRORS_COMPAT": True}):
            response = problem_details_exception_handler(exc, _context(api_rf.get("/")))

        assert response is not None
        compat = response.data["standardized_errors"]
        assert compat["type"] == "validation_error"
        assert compat["errors"] == [{"code": "required", "detail": "Required.", "attr": "title"}]

    def test_omitted_by_default(self, api_rf: APIRequestFactory) -> None:
        response = problem_details_exception_handler(
            drf_exceptions.NotFound(), _context(api_rf.get("/"))
        )

        assert response is not None
        assert "standardized_errors" not in response.data


class TestCustomRegistryKeyword:
    def test_error_type_lookup_uses_the_provided_registry_not_the_default(
        self, api_rf: APIRequestFactory
    ) -> None:
        registry = ProblemRegistry()
        registry.register(
            drf_exceptions.NotFound,
            ErrorType(code="custom_not_found", title="Nope", slug="nope", status=404),
        )

        response = problem_details_exception_handler(
            drf_exceptions.NotFound(), _context(api_rf.get("/")), registry=registry
        )

        assert response is not None
        assert response.data["code"] == "custom_not_found"
