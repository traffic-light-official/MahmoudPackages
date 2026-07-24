"""Application-raisable exceptions that map directly onto Problem Details.

:class:`ProblemAPIException` is the escape hatch for view/service code that
wants full control over the resulting
:class:`~drf_error_response_standardizer.problem.ProblemDetail` without
registering a mapping in :mod:`~drf_error_response_standardizer.registry`
first. :func:`~drf_error_response_standardizer.handler.problem_details_exception_handler`
recognizes it directly.

Two ready-made subclasses are provided for status codes Django REST
Framework does not ship an exception for: :class:`ConflictError` (409) and
:class:`UnprocessableEntityError` (422).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from rest_framework.exceptions import APIException


class ProblemAPIException(APIException):
    """Base class for exceptions that carry their own Problem Details.

    Subclass this (or raise it directly) to fully control ``title``,
    ``type``, ``status``, machine-readable ``code``, and extension members
    for a specific error condition, without touching the global registry.

    Attributes:
        title: RFC 9457 ``title`` member for this problem type. Class
            attribute default, overridable per-instance via the
            constructor.
        type_slug: Relative slug combined with the ``TYPE_BASE_URI``
            setting to build the RFC 9457 ``type`` URI. When ``None``,
            the ``type`` member defaults to ``"about:blank"``.
    """

    status_code = 400
    default_detail = "A problem occurred while processing the request."
    default_code = "problem"

    title: str = "Problem"
    type_slug: str | None = None

    def __init__(
        self,
        detail: str | None = None,
        code: str | None = None,
        *,
        title: str | None = None,
        status_code: int | None = None,
        type_slug: str | None = None,
        extensions: Mapping[str, Any] | None = None,
    ) -> None:
        """Create a problem exception.

        Args:
            detail: Human-readable explanation specific to this
                occurrence (RFC 9457 ``detail``). Defaults to
                ``default_detail`` if omitted, matching
                :class:`~rest_framework.exceptions.APIException` behavior.
            code: Machine-readable DRF error code attached to ``detail``.
                Defaults to ``default_code``.
            title: Overrides the class-level :attr:`title` for this
                instance.
            status_code: Overrides the class-level ``status_code`` for
                this instance.
            type_slug: Overrides the class-level :attr:`type_slug` for
                this instance.
            extensions: Extra RFC 9457 extension members to merge into
                the response, e.g. ``{"resource_id": order.id}``.
        """
        super().__init__(detail=detail, code=code)
        if status_code is not None:
            self.status_code = status_code
        if title is not None:
            self.title = title
        if type_slug is not None:
            self.type_slug = type_slug
        self.extensions: dict[str, Any] = dict(extensions or {})


class ConflictError(ProblemAPIException):
    """Raised when a request conflicts with the current state of a resource (409).

    Django REST Framework has no built-in exception for HTTP 409; this
    fills that gap. Typical uses: optimistic-locking version mismatches,
    duplicate submissions outside the scope of unique-constraint
    validation, or state-machine transitions that are not currently valid.
    """

    status_code = 409
    default_detail = (
        "The request could not be completed due to a conflict with the current "
        "state of the resource."
    )
    default_code = "conflict"
    title = "Conflict"
    type_slug = "conflict"


class UnprocessableEntityError(ProblemAPIException):
    """Raised for well-formed requests that fail business-rule validation (422).

    Distinct from :class:`~rest_framework.exceptions.ValidationError`
    (which this package treats as HTTP 400, syntactic/schema validation):
    use this for semantic validation failures that are not tied to a
    specific serializer field, e.g. "cannot cancel an order that has
    already shipped".
    """

    status_code = 422
    default_detail = "The request was well-formed but contains semantic errors."
    default_code = "unprocessable_entity"
    title = "Unprocessable Entity"
    type_slug = "unprocessable-entity"
