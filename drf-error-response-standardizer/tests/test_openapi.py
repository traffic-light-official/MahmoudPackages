"""Tests for the optional drf-spectacular integration."""

from __future__ import annotations

from typing import Any

from drf_error_response_standardizer.openapi import (
    PROBLEM_DETAIL_SCHEMA,
    problem_details_postprocessing_hook,
    registered_status_codes,
)


class TestProblemDetailsPostprocessingHook:
    def test_adds_problem_detail_schema_component(self) -> None:
        result: dict[str, Any] = {"paths": {}}

        problem_details_postprocessing_hook(result, generator=None, request=None, public=True)

        assert result["components"]["schemas"]["ProblemDetail"] == PROBLEM_DETAIL_SCHEMA

    def test_adds_default_error_responses_to_every_operation(self) -> None:
        result: dict[str, Any] = {
            "paths": {
                "/articles/": {
                    "get": {"responses": {"200": {"description": "OK"}}},
                }
            }
        }

        problem_details_postprocessing_hook(result, generator=None, request=None, public=True)

        responses = result["paths"]["/articles/"]["get"]["responses"]
        assert "200" in responses
        assert "404" in responses
        assert (
            responses["404"]["content"]["application/problem+json"]["schema"]["$ref"]
            == "#/components/schemas/ProblemDetail"
        )

    def test_does_not_overwrite_an_already_documented_status_code(self) -> None:
        custom_404 = {"description": "Custom not-found response."}
        result: dict[str, Any] = {
            "paths": {"/articles/": {"get": {"responses": {"404": custom_404}}}}
        }

        problem_details_postprocessing_hook(result, generator=None, request=None, public=True)

        assert result["paths"]["/articles/"]["get"]["responses"]["404"] is custom_404

    def test_ignores_non_operation_entries_in_path_item(self) -> None:
        result: dict[str, Any] = {
            "paths": {"/articles/": {"parameters": [{"name": "id"}]}},
        }

        # Should not raise even though "parameters" is a list, not an operation dict.
        problem_details_postprocessing_hook(result, generator=None, request=None, public=True)

    def test_returns_the_mutated_result(self) -> None:
        result: dict[str, Any] = {"paths": {}}

        returned = problem_details_postprocessing_hook(
            result, generator=None, request=None, public=True
        )

        assert returned is result


class TestRegisteredStatusCodes:
    def test_includes_every_builtin_status_code(self) -> None:
        codes = registered_status_codes()

        assert 400 in codes
        assert 404 in codes
        assert 500 not in codes  # server_error is not pre-registered in default_registry

    def test_is_sorted_and_deduplicated(self) -> None:
        codes = registered_status_codes()

        assert codes == sorted(set(codes))
