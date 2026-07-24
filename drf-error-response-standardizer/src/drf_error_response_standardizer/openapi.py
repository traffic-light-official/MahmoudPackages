"""``drf-spectacular`` (OpenAPI) integration.

Registers the RFC 9457 Problem Details schema as a reusable OpenAPI
component and attaches it as the response schema for every operation's
undocumented 4xx/5xx status codes, so generated API documentation and
client SDKs accurately describe error responses without every view having
to declare them manually via ``@extend_schema(responses=...)``.

Install by adding the hook to your ``SPECTACULAR_SETTINGS``::

    SPECTACULAR_SETTINGS = {
        "POSTPROCESSING_HOOKS": [
            "drf_error_response_standardizer.openapi.problem_details_postprocessing_hook",
        ],
    }
"""

from __future__ import annotations

from typing import Any

from drf_error_response_standardizer.constants import PROBLEM_CONTENT_TYPE
from drf_error_response_standardizer.registry import default_registry

#: The reusable OpenAPI schema describing every RFC 9457 Problem Details response.
PROBLEM_DETAIL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "description": "An RFC 9457 Problem Details object.",
    "properties": {
        "type": {
            "type": "string",
            "format": "uri",
            "description": "A URI reference identifying the problem type.",
        },
        "title": {
            "type": "string",
            "description": "Short, human-readable summary of the problem type.",
        },
        "status": {
            "type": "integer",
            "description": "The HTTP status code for this occurrence of the problem.",
        },
        "detail": {
            "type": "string",
            "description": "Human-readable explanation specific to this occurrence.",
        },
        "instance": {
            "type": "string",
            "format": "uri",
            "description": "A URI reference identifying this specific occurrence.",
        },
        "code": {
            "type": "string",
            "description": "Stable, machine-readable error code.",
        },
        "errors": {
            "type": "array",
            "description": "Present for validation errors: one entry per invalid field.",
            "items": {
                "type": "object",
                "properties": {
                    "pointer": {"type": "string"},
                    "detail": {"type": "string"},
                    "code": {"type": "string"},
                },
                "required": ["pointer", "detail", "code"],
            },
        },
        "correlation_id": {"type": "string"},
        "request_id": {"type": "string"},
        "trace_id": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
    },
    "required": ["type", "title", "status"],
}

_DEFAULT_STATUS_CODES = [
    "400",
    "401",
    "403",
    "404",
    "405",
    "406",
    "409",
    "415",
    "422",
    "429",
    "500",
]


def problem_details_postprocessing_hook(
    result: dict[str, Any],
    generator: Any,
    request: Any,
    public: bool,
) -> dict[str, Any]:
    """A ``drf-spectacular`` ``POSTPROCESSING_HOOKS`` entry point.

    Args:
        result: The generated OpenAPI schema document, as a plain dict.
        generator: The drf-spectacular ``SchemaGenerator`` instance. Unused;
            accepted because drf-spectacular calls every postprocessing
            hook with this fixed four-argument signature.
        request: The current request, if any. Unused, see above.
        public: Whether this is the public schema. Unused, see above.

    Returns:
        ``result``, mutated in place to add the ``ProblemDetail`` component
        and reference it from every operation's undocumented default error
        status codes.
    """
    components = result.setdefault("components", {})
    schemas = components.setdefault("schemas", {})
    schemas["ProblemDetail"] = PROBLEM_DETAIL_SCHEMA

    problem_response = {
        "description": "Error response (RFC 9457 Problem Details).",
        "content": {
            PROBLEM_CONTENT_TYPE: {"schema": {"$ref": "#/components/schemas/ProblemDetail"}}
        },
    }

    for path_item in result.get("paths", {}).values():
        for operation in path_item.values():
            if not isinstance(operation, dict) or "responses" not in operation:
                continue
            responses = operation["responses"]
            for status_code in _DEFAULT_STATUS_CODES:
                if status_code not in responses:
                    responses[status_code] = problem_response

    return result


def registered_status_codes() -> list[int]:
    """Return the distinct HTTP status codes covered by the default registry.

    Useful when building a custom postprocessing hook that should only
    document status codes this project's exception mappings can actually
    produce, rather than the fixed default list.

    Returns:
        A sorted list of unique HTTP status codes.
    """
    return sorted({error_type.status for error_type in default_registry.all_error_types()})
