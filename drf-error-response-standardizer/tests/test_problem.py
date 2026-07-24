"""Tests for :mod:`drf_error_response_standardizer.problem`."""

from __future__ import annotations

from drf_error_response_standardizer.constants import ABOUT_BLANK
from drf_error_response_standardizer.problem import ProblemDetail


class TestToDict:
    def test_minimal_problem_omits_optional_none_fields(self) -> None:
        problem = ProblemDetail(status=404, title="Resource Not Found")

        data = problem.to_dict()

        assert data == {"type": ABOUT_BLANK, "title": "Resource Not Found", "status": 404}

    def test_full_problem_includes_every_core_member(self) -> None:
        problem = ProblemDetail(
            status=400,
            title="Validation Error",
            type="https://api.example.com/problems/validation-error",
            detail="One or more fields failed validation.",
            instance="/api/articles/1/",
            code="validation_error",
        )

        data = problem.to_dict()

        assert data == {
            "type": "https://api.example.com/problems/validation-error",
            "title": "Validation Error",
            "status": 400,
            "detail": "One or more fields failed validation.",
            "instance": "/api/articles/1/",
            "code": "validation_error",
        }

    def test_extensions_are_merged_after_core_members(self) -> None:
        problem = ProblemDetail(
            status=500,
            title="Internal Server Error",
            extensions={"trace_id": "abc123", "correlation_id": "xyz789"},
        )

        data = problem.to_dict()

        assert data["trace_id"] == "abc123"
        assert data["correlation_id"] == "xyz789"

    def test_extension_cannot_shadow_a_core_member(self) -> None:
        problem = ProblemDetail(
            status=404, title="Resource Not Found", extensions={"status": 999, "title": "Hijacked"}
        )

        data = problem.to_dict()

        assert data["status"] == 404
        assert data["title"] == "Resource Not Found"


class TestWithExtensions:
    def test_returns_new_instance_with_merged_extensions(self) -> None:
        original = ProblemDetail(status=400, title="Validation Error", extensions={"a": 1})

        updated = original.with_extensions(b=2)

        assert original.extensions == {"a": 1}
        assert updated.extensions == {"a": 1, "b": 2}

    def test_overwrites_existing_extension_key(self) -> None:
        original = ProblemDetail(status=400, title="Validation Error", extensions={"a": 1})

        updated = original.with_extensions(a=99)

        assert updated.extensions == {"a": 99}

    def test_preserves_core_members(self) -> None:
        original = ProblemDetail(
            status=409,
            title="Conflict",
            type="https://api.example.com/problems/conflict",
            detail="Already shipped.",
            instance="/orders/1/",
            code="conflict",
        )

        updated = original.with_extensions(order_id=1)

        assert updated.status == 409
        assert updated.title == "Conflict"
        assert updated.type == "https://api.example.com/problems/conflict"
        assert updated.detail == "Already shipped."
        assert updated.instance == "/orders/1/"
        assert updated.code == "conflict"
