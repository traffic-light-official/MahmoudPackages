"""Custom exceptions raised by :mod:`drf_partial_response_fields`.

All exceptions in this module ultimately subclass
:class:`rest_framework.exceptions.ValidationError`, so raising them from
inside a view, serializer, or the parser (when invoked during request
handling) results in a standard DRF ``400 Bad Request`` response without
any extra wiring on the caller's part.
"""

from __future__ import annotations

from rest_framework.exceptions import ValidationError as _DRFValidationError


class PartialResponseFieldsError(_DRFValidationError):
    """Base class for all errors raised by this package.

    Catch this class if you want to handle any error originating from
    ``drf-partial-response-fields`` without depending on the more specific
    subclasses.
    """

    default_code = "partial_response_fields_error"


class InvalidFieldsParameterError(PartialResponseFieldsError):
    """Raised when the ``fields`` query parameter cannot be parsed.

    This covers syntax errors such as unbalanced parentheses, empty field
    names, invalid characters, ambiguous combinations of inclusion and
    exclusion within the same group, and expressions that exceed the
    configured maximum nesting depth.

    Args:
        message: A human-readable description of the syntax error,
            including the offending fragment where possible.

    Example:
        >>> from drf_partial_response_fields.parser import parse_fields
        >>> parse_fields("author(name")
        Traceback (most recent call last):
            ...
        drf_partial_response_fields.exceptions.InvalidFieldsParameterError: ...
    """

    default_code = "invalid_fields_parameter"

    def __init__(self, message: str) -> None:
        super().__init__({"fields": [message]}, code=self.default_code)


class UnknownFieldError(PartialResponseFieldsError):
    """Raised when a requested field does not exist on the serializer.

    Only raised when the
    :ref:`STRICT <settings-strict>` setting is enabled. When ``STRICT`` is
    disabled (the default), unknown field names are silently ignored so
    that clients cannot probe for the existence of hidden fields.

    Args:
        message: A human-readable description naming the unknown field(s).
    """

    default_code = "unknown_field"

    def __init__(self, message: str) -> None:
        super().__init__({"fields": [message]}, code=self.default_code)
