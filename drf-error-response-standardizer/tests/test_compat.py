"""Tests for :mod:`drf_error_response_standardizer.compat`."""

from __future__ import annotations

from drf_error_response_standardizer.compat import to_standardized_errors_format
from drf_error_response_standardizer.problem import ProblemDetail


class TestToStandardizedErrorsFormat:
    def test_validation_error_with_field_errors(self) -> None:
        problem = ProblemDetail(
            status=400,
            title="Validation Error",
            code="validation_error",
            detail="One or more fields failed validation.",
            extensions={
                "errors": [
                    {"pointer": "title", "detail": "Required.", "code": "required"},
                    {"pointer": "author/email", "detail": "Invalid email.", "code": "invalid"},
                ]
            },
        )

        result = to_standardized_errors_format(problem)

        assert result == {
            "type": "validation_error",
            "errors": [
                {"code": "required", "detail": "Required.", "attr": "title"},
                {"code": "invalid", "detail": "Invalid email.", "attr": "author.email"},
            ],
        }

    def test_non_field_validation_error_has_null_attr(self) -> None:
        problem = ProblemDetail(
            status=400,
            title="Validation Error",
            code="validation_error",
            detail="Cannot process this request.",
        )

        result = to_standardized_errors_format(problem)

        assert result["type"] == "client_error"
        assert result["errors"][0]["attr"] is None

    def test_client_error_below_500(self) -> None:
        problem = ProblemDetail(
            status=404, title="Resource Not Found", code="not_found", detail="Gone."
        )

        result = to_standardized_errors_format(problem)

        assert result["type"] == "client_error"
        assert result["errors"] == [{"code": "not_found", "detail": "Gone.", "attr": None}]

    def test_server_error_at_or_above_500(self) -> None:
        problem = ProblemDetail(
            status=500, title="Internal Server Error", code="server_error", detail="Oops."
        )

        result = to_standardized_errors_format(problem)

        assert result["type"] == "server_error"
