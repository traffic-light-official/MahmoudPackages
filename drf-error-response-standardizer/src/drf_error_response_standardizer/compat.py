"""Compatibility helpers for projects migrating from ``drf-standardized-errors``.

``drf-standardized-errors`` uses a response shape that predates RFC 9457:
``{"type": "validation_error" | "client_error" | "server_error", "errors":
[{"code", "detail", "attr"}, ...]}``. This module renders that exact shape
from a :class:`~drf_error_response_standardizer.problem.ProblemDetail`, so a
project migrating to this package can emit it as an additional
``standardized_errors`` extension member during a transition window
(enabled via the ``STANDARDIZED_ERRORS_COMPAT`` setting) without giving up
the stronger RFC 9457 guarantees of the primary response body.
"""

from __future__ import annotations

from typing import Any

from drf_error_response_standardizer.problem import ProblemDetail

_VALIDATION_STATUS = 400
_SERVER_ERROR_THRESHOLD = 500


def to_standardized_errors_format(problem: ProblemDetail) -> dict[str, Any]:
    """Render ``problem`` in the ``drf-standardized-errors`` response shape.

    Args:
        problem: A fully-built problem, including any ``errors`` extension
            member produced by
            :func:`~drf_error_response_standardizer.handler.problem_details_exception_handler`
            for validation errors.

    Returns:
        A dict shaped like ``{"type": ..., "errors": [{"code", "detail",
        "attr"}, ...]}``, matching ``drf-standardized-errors``' documented
        format. ``attr`` uses dot-separated paths (``"author.email"``)
        rather than this package's slash-separated JSON Pointers, matching
        ``drf-standardized-errors`` conventions exactly.
    """
    field_errors = problem.extensions.get("errors")
    if problem.status == _VALIDATION_STATUS and field_errors:
        coarse_type = "validation_error"
        errors = [
            {
                "code": item["code"],
                "detail": item["detail"],
                "attr": item["pointer"].replace("/", ".") or None,
            }
            for item in field_errors
        ]
    else:
        coarse_type = (
            "server_error" if problem.status >= _SERVER_ERROR_THRESHOLD else "client_error"
        )
        errors = [{"code": problem.code, "detail": problem.detail, "attr": None}]
    return {"type": coarse_type, "errors": errors}
