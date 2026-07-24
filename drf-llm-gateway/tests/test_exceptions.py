"""Tests for the exception hierarchy."""

from __future__ import annotations

from rest_framework.exceptions import APIException
from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied
from rest_framework.exceptions import ValidationError as DRFValidationError

from drf_llm_gateway.exceptions import (
    LLMGatewayError,
    SchemaGenerationError,
    ToolExecutionError,
    ToolNotFoundError,
    ToolPermissionDeniedError,
    ToolRegistrationError,
    ToolValidationError,
)


class TestExceptionHierarchy:
    def test_schema_generation_error_is_a_value_error(self) -> None:
        assert issubclass(SchemaGenerationError, ValueError)
        assert issubclass(SchemaGenerationError, LLMGatewayError)

    def test_tool_registration_error_is_a_value_error(self) -> None:
        assert issubclass(ToolRegistrationError, ValueError)

    def test_tool_not_found_is_an_api_exception_with_404(self) -> None:
        exc = ToolNotFoundError("missing")
        assert isinstance(exc, APIException)
        assert exc.status_code == 404
        assert "missing" in str(exc.detail)

    def test_tool_validation_error_is_a_drf_validation_error(self) -> None:
        exc = ToolValidationError({"field": ["required"]})
        assert isinstance(exc, DRFValidationError)
        assert isinstance(exc, ToolExecutionError)

    def test_tool_permission_denied_is_a_drf_permission_denied(self) -> None:
        exc = ToolPermissionDeniedError("secret_tool")
        assert isinstance(exc, DRFPermissionDenied)
        assert exc.status_code == 403
        assert "secret_tool" in str(exc.detail)
