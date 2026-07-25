"""Tests for :mod:`drf_api_versioning.exceptions`."""

from __future__ import annotations

import datetime

from rest_framework import status
from rest_framework.exceptions import APIException

from drf_api_versioning.exceptions import APIVersionSunsetError, UnknownAPIVersionError


class TestUnknownAPIVersionError:
    def test_is_an_api_exception(self) -> None:
        assert issubclass(UnknownAPIVersionError, APIException)

    def test_status_code_is_404(self) -> None:
        assert UnknownAPIVersionError("v9", ("v1", "v2")).status_code == status.HTTP_404_NOT_FOUND

    def test_detail_names_the_bad_version(self) -> None:
        error = UnknownAPIVersionError("v9", ("v1", "v2"))
        assert "v9" in str(error)

    def test_detail_lists_known_versions(self) -> None:
        error = UnknownAPIVersionError("v9", ("v1", "v2"))
        assert "v1" in str(error)
        assert "v2" in str(error)


class TestAPIVersionSunsetError:
    def test_is_an_api_exception(self) -> None:
        assert issubclass(APIVersionSunsetError, APIException)

    def test_status_code_is_410(self) -> None:
        error = APIVersionSunsetError("v1", datetime.date(2020, 1, 1))
        assert error.status_code == status.HTTP_410_GONE

    def test_detail_names_the_version_and_date(self) -> None:
        error = APIVersionSunsetError("v1", datetime.date(2020, 1, 1))
        assert "v1" in str(error)
        assert "2020-01-01" in str(error)
