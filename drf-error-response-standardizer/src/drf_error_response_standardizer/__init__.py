"""RFC 9457 Problem Details standardization for Django REST Framework.

The public API is intentionally small. Most projects only need:

* :func:`~drf_error_response_standardizer.handler.problem_details_exception_handler`
  set as DRF's ``EXCEPTION_HANDLER``.
* :class:`~drf_error_response_standardizer.middleware.CorrelationIdMiddleware`
  added to ``MIDDLEWARE``.
* :func:`~drf_error_response_standardizer.registry.register` (or
  :class:`~drf_error_response_standardizer.exceptions.ProblemAPIException`)
  for application-specific error types.

See ``docs/quickstart.md`` for a complete end-to-end example.
"""

from __future__ import annotations

from drf_error_response_standardizer.catalog import build_catalog, render_json, render_markdown
from drf_error_response_standardizer.codes import BUILTIN_ERROR_TYPES, ErrorType
from drf_error_response_standardizer.compat import to_standardized_errors_format
from drf_error_response_standardizer.exceptions import (
    ConflictError,
    ProblemAPIException,
    UnprocessableEntityError,
)
from drf_error_response_standardizer.handler import problem_details_exception_handler
from drf_error_response_standardizer.localization import (
    activate_for_request,
    resolve_language,
    translate,
)
from drf_error_response_standardizer.middleware import (
    CorrelationIdMiddleware,
    get_correlation_id,
    get_request_id,
    get_trace_id,
)
from drf_error_response_standardizer.normalize import NormalizedError, normalize_validation_error
from drf_error_response_standardizer.openapi import (
    PROBLEM_DETAIL_SCHEMA,
    problem_details_postprocessing_hook,
    registered_status_codes,
)
from drf_error_response_standardizer.problem import ProblemDetail
from drf_error_response_standardizer.registry import (
    ProblemRegistry,
    default_registry,
    register,
    register_builder,
)
from drf_error_response_standardizer.settings import app_settings, get_setting

__version__ = "1.0.0"

__all__ = [
    "BUILTIN_ERROR_TYPES",
    "PROBLEM_DETAIL_SCHEMA",
    "ConflictError",
    "CorrelationIdMiddleware",
    "ErrorType",
    "NormalizedError",
    "ProblemAPIException",
    "ProblemDetail",
    "ProblemRegistry",
    "UnprocessableEntityError",
    "__version__",
    "activate_for_request",
    "app_settings",
    "build_catalog",
    "default_registry",
    "get_correlation_id",
    "get_request_id",
    "get_setting",
    "get_trace_id",
    "normalize_validation_error",
    "problem_details_exception_handler",
    "problem_details_postprocessing_hook",
    "register",
    "register_builder",
    "registered_status_codes",
    "render_json",
    "render_markdown",
    "resolve_language",
    "to_standardized_errors_format",
    "translate",
]
