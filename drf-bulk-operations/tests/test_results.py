"""Tests for :mod:`drf_bulk_operations.results`."""

from __future__ import annotations

from rest_framework import status

from drf_bulk_operations.results import ItemResult, build_bulk_response


class TestItemResultAsDict:
    def test_success_includes_data_not_errors(self) -> None:
        result = ItemResult(index=0, success=True, data={"id": 1})
        assert result.as_dict() == {"index": 0, "status": "success", "data": {"id": 1}}

    def test_failure_includes_errors_not_data(self) -> None:
        result = ItemResult(index=1, success=False, errors={"title": ["required"]})
        assert result.as_dict() == {
            "index": 1,
            "status": "error",
            "errors": {"title": ["required"]},
        }


class TestBuildBulkResponse:
    def test_all_success_returns_plain_data_list(self) -> None:
        results = [
            ItemResult(index=0, success=True, data={"id": 1}),
            ItemResult(index=1, success=True, data={"id": 2}),
        ]
        response = build_bulk_response(results, all_success_status=status.HTTP_201_CREATED)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data == [{"id": 1}, {"id": 2}]

    def test_all_success_with_empty_body_returns_no_data(self) -> None:
        results = [ItemResult(index=0, success=True), ItemResult(index=1, success=True)]
        response = build_bulk_response(
            results, all_success_status=status.HTTP_204_NO_CONTENT, empty_success_body=True
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.data is None

    def test_mixed_results_return_207_multi_status(self) -> None:
        results = [
            ItemResult(index=0, success=True, data={"id": 1}),
            ItemResult(index=1, success=False, errors={"title": ["required"]}),
        ]
        response = build_bulk_response(results, all_success_status=status.HTTP_201_CREATED)
        assert response.status_code == status.HTTP_207_MULTI_STATUS
        assert response.data == [
            {"index": 0, "status": "success", "data": {"id": 1}},
            {"index": 1, "status": "error", "errors": {"title": ["required"]}},
        ]

    def test_all_failure_returns_400(self) -> None:
        results = [
            ItemResult(index=0, success=False, errors={"title": ["required"]}),
            ItemResult(index=1, success=False, errors={"title": ["required"]}),
        ]
        response = build_bulk_response(results, all_success_status=status.HTTP_201_CREATED)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert all(item["status"] == "error" for item in response.data)

    def test_empty_results_list_is_treated_as_all_success(self) -> None:
        response = build_bulk_response([], all_success_status=status.HTTP_201_CREATED)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data == []
