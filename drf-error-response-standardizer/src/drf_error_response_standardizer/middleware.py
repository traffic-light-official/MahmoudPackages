"""Correlation, request, and trace ID propagation middleware.

:class:`CorrelationIdMiddleware` is deliberately independent from DRF's
exception handling: it runs for *every* request/response, not just error
responses, so a correlation ID is available for logging and tracing on the
success path too, and so
:func:`~drf_error_response_standardizer.handler.problem_details_exception_handler`
can simply read the IDs back off ``request`` rather than parsing headers
itself.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import cast

from django.http import HttpRequest, HttpResponse

from drf_error_response_standardizer.constants import (
    CORRELATION_ID_HEADER,
    CORRELATION_ID_META_KEY,
    REQUEST_CORRELATION_ID_ATTR,
    REQUEST_ID_HEADER,
    REQUEST_ID_META_KEY,
    REQUEST_REQUEST_ID_ATTR,
    REQUEST_TRACE_ID_ATTR,
    TRACEPARENT_META_KEY,
)

GetResponse = Callable[[HttpRequest], HttpResponse]


class CorrelationIdMiddleware:
    """Assigns correlation, request, and trace IDs to every request/response.

    - ``correlation_id``: taken from the incoming ``X-Correlation-ID``
      header if present (preserving a caller's or gateway's ID across an
      entire user-facing transaction), otherwise a new UUID4 is generated.
    - ``request_id``: taken from the incoming ``X-Request-ID`` header if
      present, otherwise a new UUID4 is generated. Unlike the correlation
      ID, this identifies exactly one HTTP request/response pair, even
      within a single logical transaction.
    - ``trace_id``: extracted from an incoming W3C ``traceparent`` header
      (see https://www.w3.org/TR/trace-context/) if present and
      well-formed, ``None`` otherwise. This middleware never *generates* a
      trace ID - that is the responsibility of a tracing SDK.

    Both the correlation ID and request ID are echoed back as response
    headers so callers can correlate their own logs against server-side
    logs on success responses too, not only on errors. Use
    :func:`get_correlation_id`, :func:`get_request_id`, and
    :func:`get_trace_id` to read the values back off a request elsewhere
    in the application (they are stored as plain instance attributes, so
    reading them directly off ``request`` also works, but the accessors
    give a stable, typed API).

    Add this middleware near the top of ``MIDDLEWARE`` (before anything
    that logs the request) so the IDs are available to every downstream
    middleware, view, and log line::

        MIDDLEWARE = [
            "drf_error_response_standardizer.middleware.CorrelationIdMiddleware",
            # ... the rest of your middleware ...
        ]
    """

    def __init__(self, get_response: GetResponse) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        correlation_id = request.META.get(CORRELATION_ID_META_KEY) or str(uuid.uuid4())
        request_id = request.META.get(REQUEST_ID_META_KEY) or str(uuid.uuid4())
        trace_id = _extract_trace_id(request.META.get(TRACEPARENT_META_KEY))

        setattr(request, REQUEST_CORRELATION_ID_ATTR, correlation_id)
        setattr(request, REQUEST_REQUEST_ID_ATTR, request_id)
        setattr(request, REQUEST_TRACE_ID_ATTR, trace_id)

        response = self.get_response(request)

        response[CORRELATION_ID_HEADER] = correlation_id
        response[REQUEST_ID_HEADER] = request_id
        return response


def get_correlation_id(request: HttpRequest) -> str | None:
    """Return the correlation ID assigned by :class:`CorrelationIdMiddleware`.

    Args:
        request: The current request.

    Returns:
        The correlation ID, or ``None`` if the middleware is not installed.
    """
    return cast("str | None", getattr(request, REQUEST_CORRELATION_ID_ATTR, None))


def get_request_id(request: HttpRequest) -> str | None:
    """Return the request ID assigned by :class:`CorrelationIdMiddleware`.

    Args:
        request: The current request.

    Returns:
        The request ID, or ``None`` if the middleware is not installed.
    """
    return cast("str | None", getattr(request, REQUEST_REQUEST_ID_ATTR, None))


def get_trace_id(request: HttpRequest) -> str | None:
    """Return the W3C trace ID extracted by :class:`CorrelationIdMiddleware`.

    Args:
        request: The current request.

    Returns:
        The 32-character hex trace ID, or ``None`` if the middleware is
        not installed or no valid ``traceparent`` header was present.
    """
    return cast("str | None", getattr(request, REQUEST_TRACE_ID_ATTR, None))


def _extract_trace_id(traceparent: str | None) -> str | None:
    """Extract the trace-id field from a W3C ``traceparent`` header value.

    Format: ``{version}-{trace-id}-{parent-id}-{trace-flags}``, e.g.
    ``00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01``. Returns
    ``None`` if the header is absent or does not match the expected shape
    rather than raising: a malformed tracing header should never break a
    request.
    """
    if not traceparent:
        return None
    parts = traceparent.split("-")
    if len(parts) != 4 or len(parts[1]) != 32:
        return None
    return parts[1]
