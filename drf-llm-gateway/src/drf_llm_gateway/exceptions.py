"""Custom exceptions raised by :mod:`drf_llm_gateway`.

Runtime errors raised while *executing* a tool (as opposed to generating
its schema) subclass :class:`rest_framework.exceptions.APIException` so
they translate into sensible HTTP responses if surfaced through a DRF view;
schema-generation errors are plain :class:`ValueError` subclasses since
they represent programming mistakes discovered at startup/registration
time, not runtime request errors.
"""

from __future__ import annotations

from rest_framework.exceptions import APIException
from rest_framework.exceptions import PermissionDenied as _DRFPermissionDenied
from rest_framework.exceptions import ValidationError as _DRFValidationError


class LLMGatewayError(Exception):
    """Base class for all errors raised by this package."""


class SchemaGenerationError(LLMGatewayError, ValueError):
    """Raised when a serializer cannot be converted to JSON Schema.

    The exception message describes what could not be converted and why
    (e.g. an invalid ``mode``, or nesting beyond ``MAX_SCHEMA_DEPTH``).
    """


class ToolRegistrationError(LLMGatewayError, ValueError):
    """Raised when :func:`~drf_llm_gateway.registry.expose_as_tool` or
    :meth:`~drf_llm_gateway.registry.ToolRegistry.register` is used
    incorrectly — e.g. duplicate tool names, or an unsupported action.

    The exception message names the specific registration problem
    encountered.
    """


class ToolExecutionError(LLMGatewayError, APIException):
    """Base class for errors raised while executing a registered tool."""

    default_code = "tool_execution_error"


class ToolNotFoundError(ToolExecutionError):
    """Raised when :func:`~drf_llm_gateway.executor.execute_tool` is asked
    to run a tool name that isn't registered.

    Args:
        name: The unrecognized tool name.
    """

    status_code = 404
    default_code = "tool_not_found"

    def __init__(self, name: str) -> None:
        super().__init__(detail=f"No tool named {name!r} is registered.", code=self.default_code)


class ToolValidationError(ToolExecutionError, _DRFValidationError):
    """Raised when the arguments passed to a tool fail serializer validation.

    The underlying :attr:`detail` mirrors the structure DRF's own
    :class:`~rest_framework.exceptions.ValidationError` produces, so
    field-level error messages are preserved.
    """

    default_code = "tool_validation_error"


class ToolPermissionDeniedError(ToolExecutionError, _DRFPermissionDenied):
    """Raised when the calling identity fails a tool's permission checks.

    Args:
        name: The tool name that was denied.
    """

    default_code = "tool_permission_denied"

    def __init__(self, name: str) -> None:
        super().__init__(detail=f"Permission denied for tool {name!r}.", code=self.default_code)
