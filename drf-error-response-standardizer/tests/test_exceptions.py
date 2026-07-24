"""Tests for :mod:`drf_error_response_standardizer.exceptions`."""

from __future__ import annotations

from drf_error_response_standardizer.exceptions import (
    ConflictError,
    ProblemAPIException,
    UnprocessableEntityError,
)


class TestProblemAPIException:
    def test_uses_class_defaults(self) -> None:
        exc = ProblemAPIException()

        assert exc.status_code == 400
        assert exc.title == "Problem"
        assert exc.type_slug is None
        assert str(exc.detail) == "A problem occurred while processing the request."
        assert exc.extensions == {}

    def test_constructor_overrides_are_applied(self) -> None:
        exc = ProblemAPIException(
            "Custom detail.",
            code="custom_code",
            title="Custom Title",
            status_code=422,
            type_slug="custom-problem",
            extensions={"resource_id": 7},
        )

        assert str(exc.detail) == "Custom detail."
        assert exc.detail.code == "custom_code"  # type: ignore[union-attr]
        assert exc.title == "Custom Title"
        assert exc.status_code == 422
        assert exc.type_slug == "custom-problem"
        assert exc.extensions == {"resource_id": 7}

    def test_extensions_default_to_empty_dict_per_instance(self) -> None:
        first = ProblemAPIException()
        second = ProblemAPIException()
        first.extensions["leaked"] = True

        assert second.extensions == {}


class TestConflictError:
    def test_defaults(self) -> None:
        exc = ConflictError()

        assert exc.status_code == 409
        assert exc.title == "Conflict"
        assert exc.type_slug == "conflict"
        assert exc.get_codes() == "conflict"

    def test_custom_detail(self) -> None:
        exc = ConflictError("Order already shipped.")

        assert str(exc.detail) == "Order already shipped."


class TestUnprocessableEntityError:
    def test_defaults(self) -> None:
        exc = UnprocessableEntityError()

        assert exc.status_code == 422
        assert exc.title == "Unprocessable Entity"
        assert exc.type_slug == "unprocessable-entity"
        assert exc.get_codes() == "unprocessable_entity"
