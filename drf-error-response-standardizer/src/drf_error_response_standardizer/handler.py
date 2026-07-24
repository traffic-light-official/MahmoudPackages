"""The RFC 9457 Problem Details exception handler.

Install by pointing DRF's ``EXCEPTION_HANDLER`` setting at
:func:`problem_details_exception_handler`::

    REST_FRAMEWORK = {
        "EXCEPTION_HANDLER": (
            "drf_error_response_standardizer.handler.problem_details_exception_handler"
        ),
    }

Resolution order for a raised exception:

1. :class:`~drf_error_response_standardizer.exceptions.ProblemAPIException`
   (or a subclass) - used as-is.
2. A custom builder registered via
   :func:`~drf_error_response_standardizer.registry.register_builder`.
3. :class:`~rest_framework.exceptions.ValidationError` - expanded into a
   field-level ``errors`` array (unless ``EXPAND_VALIDATION_ERRORS`` is
   ``False``).
4. Any other :class:`~rest_framework.exceptions.APIException` - mapped via
   a registered :class:`~drf_error_response_standardizer.codes.ErrorType`
   if one exists for its class (or a base class), otherwise built directly
   from the exception's own ``detail``/``status_code``/error codes.
5. Any exception not covered above (including
   :class:`django.http.Http404` and :class:`django.core.exceptions.PermissionDenied`,
   both pre-registered in the default registry) - mapped via a registered
   :class:`~drf_error_response_standardizer.codes.ErrorType` if found.
6. Anything else - a generic 500, unless ``CATCH_ALL_EXCEPTIONS`` is
   ``False``, in which case ``None`` is returned so Django's own
   uncaught-exception handling takes over, matching the return contract of
   DRF's built-in ``exception_handler``.
"""

from __future__ import annotations

import datetime as dt
import re
from typing import Any

from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import set_rollback

from drf_error_response_standardizer.codes import BUILTIN_ERROR_TYPES, ErrorType
from drf_error_response_standardizer.compat import to_standardized_errors_format
from drf_error_response_standardizer.constants import ABOUT_BLANK
from drf_error_response_standardizer.exceptions import ProblemAPIException
from drf_error_response_standardizer.localization import activate_for_request, translate
from drf_error_response_standardizer.middleware import (
    get_correlation_id,
    get_request_id,
    get_trace_id,
)
from drf_error_response_standardizer.normalize import normalize_validation_error
from drf_error_response_standardizer.problem import ProblemDetail
from drf_error_response_standardizer.registry import ProblemRegistry, default_registry
from drf_error_response_standardizer.settings import get_setting

_CAMEL_CASE_BOUNDARY = re.compile(r"(?<!^)(?=[A-Z])")


def problem_details_exception_handler(
    exc: Exception, context: dict[str, Any], *, registry: ProblemRegistry | None = None
) -> Response | None:
    """DRF ``EXCEPTION_HANDLER`` producing RFC 9457 Problem Details responses.

    Args:
        exc: The exception raised by the view.
        context: The context dict DRF passes to exception handlers,
            containing ``"view"``, ``"args"``, ``"kwargs"``, and
            ``"request"``.
        registry: The :class:`~drf_error_response_standardizer.registry.ProblemRegistry`
            to resolve custom exception mappings from. Defaults to
            :data:`~drf_error_response_standardizer.registry.default_registry`.
            Exposed as a keyword argument so a project can bind its own
            registry with ``functools.partial`` instead of needing a
            second copy of this function.

    Returns:
        A DRF ``Response`` rendering the problem as JSON (or
        ``application/problem+json``, per the ``MEDIA_TYPE`` setting), or
        ``None`` if ``exc`` is not handleable - see the module docstring
        for the full resolution order.
    """
    active_registry = registry or default_registry
    request = context.get("request")

    if request is not None:
        with activate_for_request(request):
            problem = _build_problem(exc, active_registry)
    else:
        problem = _build_problem(exc, active_registry)

    if problem is None:
        return None

    set_rollback()

    if request is not None:
        problem = _attach_request_extensions(problem, request)

    if get_setting("STANDARDIZED_ERRORS_COMPAT"):
        problem = problem.with_extensions(
            standardized_errors=to_standardized_errors_format(problem)
        )

    headers = _extract_headers(exc)
    media_type = get_setting("MEDIA_TYPE")
    return Response(
        problem.to_dict(), status=problem.status, content_type=media_type, headers=headers
    )


def _build_problem(  # noqa: PLR0911
    exc: Exception, registry: ProblemRegistry
) -> ProblemDetail | None:
    if isinstance(exc, ProblemAPIException):
        return _from_problem_api_exception(exc)

    builder = registry.find_builder(exc)
    if builder is not None:
        return builder(exc)

    if isinstance(exc, ValidationError) and get_setting("EXPAND_VALIDATION_ERRORS"):
        return _from_validation_error(exc, registry)

    if isinstance(exc, APIException):
        return _from_api_exception(exc, registry)

    error_type = registry.find_error_type(exc)
    if error_type is not None:
        detail = str(exc) or None
        return _problem_from_error_type(error_type, detail=detail)

    if not get_setting("CATCH_ALL_EXCEPTIONS"):
        return None

    return _problem_from_error_type(
        BUILTIN_ERROR_TYPES["server_error"],
        detail=translate(get_setting("SERVER_ERROR_DETAIL")),
    )


def _from_problem_api_exception(exc: ProblemAPIException) -> ProblemDetail:
    type_uri = _build_type_uri(exc.type_slug) if exc.type_slug else ABOUT_BLANK
    return ProblemDetail(
        status=exc.status_code,
        title=translate(exc.title),
        type=type_uri,
        detail=_flatten_detail(exc.detail),
        code=_first_code(exc.get_codes()),
        extensions=dict(exc.extensions),
    )


def _from_validation_error(exc: ValidationError, registry: ProblemRegistry) -> ProblemDetail:
    error_type = registry.find_error_type(exc) or BUILTIN_ERROR_TYPES["validation_error"]
    normalized = normalize_validation_error(exc)

    extensions: dict[str, Any] = {}
    if len(normalized) == 1 and not normalized[0].pointer:
        detail = normalized[0].detail
    else:
        detail = translate("One or more fields failed validation.")
        if normalized:
            extensions["errors"] = [item.to_dict() for item in normalized]

    return ProblemDetail(
        status=error_type.status,
        title=translate(error_type.title),
        type=_build_type_uri(error_type.slug),
        detail=detail,
        code=error_type.code,
        extensions=extensions,
    )


def _from_api_exception(exc: APIException, registry: ProblemRegistry) -> ProblemDetail:
    error_type = registry.find_error_type(exc)
    if error_type is not None:
        title = translate(error_type.title)
        code = error_type.code
        status = error_type.status
        type_uri = _build_type_uri(error_type.slug)
    else:
        title = translate(_humanize_exception_name(exc))
        code = _first_code(exc.get_codes())
        status = exc.status_code
        type_uri = ABOUT_BLANK

    return ProblemDetail(
        status=status,
        title=title,
        type=type_uri,
        detail=_flatten_detail(exc.detail),
        code=code,
    )


def _problem_from_error_type(error_type: ErrorType, *, detail: str | None) -> ProblemDetail:
    return ProblemDetail(
        status=error_type.status,
        title=translate(error_type.title),
        type=_build_type_uri(error_type.slug),
        detail=detail,
        code=error_type.code,
    )


def _attach_request_extensions(problem: ProblemDetail, request: Any) -> ProblemDetail:
    instance = problem.instance
    if instance is None and get_setting("INCLUDE_INSTANCE"):
        instance = getattr(request, "path", None)

    extensions: dict[str, Any] = dict(problem.extensions)
    if get_setting("INCLUDE_CORRELATION_ID"):
        correlation_id = get_correlation_id(request)
        if correlation_id:
            extensions["correlation_id"] = correlation_id
    if get_setting("INCLUDE_REQUEST_ID"):
        request_id = get_request_id(request)
        if request_id:
            extensions["request_id"] = request_id
    if get_setting("INCLUDE_TRACE_ID"):
        trace_id = get_trace_id(request)
        if trace_id:
            extensions["trace_id"] = trace_id
    if get_setting("INCLUDE_TIMESTAMP"):
        extensions["timestamp"] = dt.datetime.now(dt.timezone.utc).isoformat()

    return ProblemDetail(
        status=problem.status,
        title=problem.title,
        type=problem.type,
        detail=problem.detail,
        instance=instance,
        code=problem.code,
        extensions=extensions,
    )


def _extract_headers(exc: Exception) -> dict[str, str]:
    """Mirror DRF's own header handling for ``WWW-Authenticate`` and ``Retry-After``.

    DRF's ``APIView.handle_exception`` sets ``exc.auth_header`` on
    ``NotAuthenticated``/``AuthenticationFailed`` instances, and
    ``Throttled.__init__`` always sets ``exc.wait``, before the configured
    exception handler ever runs. Preserving both headers here keeps this
    handler a drop-in replacement for DRF's default one.
    """
    headers: dict[str, str] = {}
    auth_header = getattr(exc, "auth_header", None)
    if auth_header:
        headers["WWW-Authenticate"] = str(auth_header)
    wait = getattr(exc, "wait", None)
    if wait is not None:
        headers["Retry-After"] = str(int(wait))
    return headers


def _build_type_uri(slug: str) -> str:
    base_uri = get_setting("TYPE_BASE_URI")
    if not base_uri:
        return ABOUT_BLANK
    return f"{base_uri}{slug}"


def _flatten_detail(detail: Any) -> str:
    if isinstance(detail, (list, tuple)):
        return "; ".join(_flatten_detail(item) for item in detail)
    if isinstance(detail, dict):
        return "; ".join(f"{key}: {_flatten_detail(value)}" for key, value in detail.items())
    return str(detail)


def _first_code(codes: Any) -> str:
    if isinstance(codes, str):
        return codes
    if isinstance(codes, list):
        for item in codes:
            found = _first_code(item)
            if found:
                return found
        return "error"
    if isinstance(codes, dict):
        for item in codes.values():
            found = _first_code(item)
            if found:
                return found
        return "error"
    return "error"


def _humanize_exception_name(exc: Exception) -> str:
    """Best-effort ``"NotAcceptable"`` -> ``"Not Acceptable"`` conversion.

    Only used as a last-resort title for exception classes that have no
    registered :class:`~drf_error_response_standardizer.codes.ErrorType`;
    register one explicitly for anything user-facing rather than relying
    on this.
    """
    return _CAMEL_CASE_BOUNDARY.sub(" ", type(exc).__name__)
