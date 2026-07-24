"""Tests for :mod:`drf_error_response_standardizer.normalize`."""

from __future__ import annotations

from rest_framework.exceptions import ErrorDetail, ValidationError

from drf_error_response_standardizer.normalize import normalize_validation_error


class TestNormalizeValidationError:
    def test_flat_field_errors(self) -> None:
        exc = ValidationError(
            {
                "title": [ErrorDetail("This field is required.", code="required")],
                "body": [ErrorDetail("This field may not be blank.", code="blank")],
            }
        )

        result = {e.pointer: (e.detail, e.code) for e in normalize_validation_error(exc)}

        assert result == {
            "title": ("This field is required.", "required"),
            "body": ("This field may not be blank.", "blank"),
        }

    def test_nested_serializer_errors_use_slash_pointers(self) -> None:
        exc = ValidationError(
            {
                "author": {"email": [ErrorDetail("Enter a valid email address.", code="invalid")]},
            }
        )

        result = normalize_validation_error(exc)

        assert len(result) == 1
        assert result[0].pointer == "author/email"
        assert result[0].code == "invalid"

    def test_deeply_nested_errors(self) -> None:
        exc = ValidationError(
            {
                "company": {
                    "address": {"city": [ErrorDetail("This field is required.", code="required")]}
                }
            }
        )

        result = normalize_validation_error(exc)

        assert len(result) == 1
        assert result[0].pointer == "company/address/city"

    def test_many_true_list_serializer_errors_use_index_pointers(self) -> None:
        exc = ValidationError(
            [
                {},
                {"title": [ErrorDetail("This field is required.", code="required")]},
                {},
            ]
        )

        result = normalize_validation_error(exc)

        assert len(result) == 1
        assert result[0].pointer == "1/title"

    def test_multiple_leaf_messages_on_a_single_field(self) -> None:
        exc = ValidationError(
            {
                "password": [
                    ErrorDetail("This password is too short.", code="password_too_short"),
                    ErrorDetail("This password is too common.", code="password_too_common"),
                ]
            }
        )

        result = normalize_validation_error(exc)

        assert len(result) == 2
        assert all(e.pointer == "password" for e in result)
        assert {e.code for e in result} == {"password_too_short", "password_too_common"}

    def test_non_field_error_has_empty_pointer(self) -> None:
        exc = ValidationError("Cannot process this request.")

        result = normalize_validation_error(exc)

        assert len(result) == 1
        assert result[0].pointer == ""
        assert result[0].detail == "Cannot process this request."

    def test_error_without_code_attribute_defaults_to_invalid(self) -> None:
        exc = ValidationError({"title": ["A plain string, not an ErrorDetail."]})

        result = normalize_validation_error(exc)

        assert result[0].code == "invalid"

    def test_list_field_index_errors(self) -> None:
        exc = ValidationError(
            {
                "tags": {
                    0: [
                        ErrorDetail(
                            "Ensure this value has at most 20 characters.", code="max_length"
                        )
                    ]
                }
            }
        )

        result = normalize_validation_error(exc)

        assert len(result) == 1
        assert result[0].pointer == "tags/0"


class TestNormalizedErrorToDict:
    def test_to_dict_shape(self) -> None:
        exc = ValidationError({"title": [ErrorDetail("Required.", code="required")]})

        entry = normalize_validation_error(exc)[0]

        assert entry.to_dict() == {"pointer": "title", "detail": "Required.", "code": "required"}
