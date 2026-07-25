"""Exceptions raised by :mod:`drf_api_versioning`."""

from __future__ import annotations

from rest_framework import status
from rest_framework.exceptions import APIException


class UnknownAPIVersionError(APIException):
    """Raised when a request resolves to a version not in the registry.

    ``status_code`` defaults to 404, matching most versioning schemes'
    own convention for "no such version" - but the versioning classes in
    :mod:`drf_api_versioning.versioning` pass through the *wrapped*
    scheme's native status code (406 for
    :class:`~drf_api_versioning.versioning.AcceptHeaderVersioning`,
    since that scheme's failure mode is a content-negotiation mismatch,
    not a missing resource), so the HTTP semantics DRF's own classes
    already chose are preserved even though the message is richer.
    """

    status_code = status.HTTP_404_NOT_FOUND
    default_code = "unknown_api_version"

    def __init__(
        self, version: str, known_versions: tuple[str, ...], *, status_code: int | None = None
    ) -> None:
        detail = (
            f"Unknown API version {version!r}. Supported versions: {', '.join(known_versions)}."
        )
        super().__init__(detail=detail, code=self.default_code)
        if status_code is not None:
            # djangorestframework-stubs types `status_code` as a per-class
            # Literal (e.g. Literal[404]); a dynamic override is legitimate
            # here (see the class docstring) but not expressible in that
            # stub's type.
            self.status_code = status_code  # type: ignore[assignment]


class APIVersionSunsetError(APIException):
    """Raised when a request resolves to a version past its sunset date."""

    status_code = status.HTTP_410_GONE
    default_code = "api_version_sunset"

    def __init__(self, version: str, sunset_on: object) -> None:
        detail = (
            f"API version {version!r} has been sunset as of {sunset_on} "
            "and is no longer available."
        )
        super().__init__(detail=detail, code=self.default_code)
