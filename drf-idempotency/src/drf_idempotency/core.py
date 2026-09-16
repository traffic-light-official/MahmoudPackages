"""Shared request-processing logic used by both the middleware and the decorator.

Both integration points reduce to the same operation: given a request and
a zero-argument callable that executes the "real" view, decide whether to
run it (and store its result) or replay a previously stored result — see
:func:`process_idempotent_request`.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import timedelta
from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse, StreamingHttpResponse
from django.test.signals import setting_changed
from django.utils.module_loading import import_string
from rest_framework.request import Request

from drf_idempotency.backends.base import BaseBackend, StoredRecord
from drf_idempotency.exceptions import (
    ConcurrentRequestError,
    IdempotencyError,
    IdempotencyKeyReuseError,
    InvalidIdempotencyKeyError,
    MissingIdempotencyKeyError,
)
from drf_idempotency.fingerprint import compute_fingerprint
from drf_idempotency.settings import get_setting

_KEY_PATTERN = re.compile(r"^[A-Za-z0-9._~:-]+$")
_EXCLUDED_RESPONSE_HEADERS = frozenset({"content-length", "connection", "set-cookie"})

_backend_instance: BaseBackend | None = None


def get_backend() -> BaseBackend:
    """Return the configured backend instance, constructing it on first use.

    The instance is cached for the lifetime of the process (or until the
    ``IDEMPOTENCY`` setting changes, e.g. via ``@override_settings`` in
    tests) so that stateful backends (like a Redis client's connection
    pool) aren't rebuilt on every request.

    Returns:
        The singleton backend instance.
    """
    global _backend_instance
    if _backend_instance is None:
        backend_cls = import_string(get_setting("BACKEND"))
        _backend_instance = backend_cls(**get_setting("BACKEND_OPTIONS"))
    return _backend_instance


def _reset_backend(*, sender: Any, setting: str, **kwargs: Any) -> None:
    if setting == "IDEMPOTENCY":
        global _backend_instance
        _backend_instance = None


setting_changed.connect(_reset_backend)


def validate_key(key: str) -> None:
    """Validate a client-supplied idempotency key.

    Args:
        key: The raw header value to validate.

    Raises:
        drf_idempotency.exceptions.InvalidIdempotencyKeyError: If the key
            is empty, too long, or contains characters outside
            ``[A-Za-z0-9._~:-]``.
    """
    if not key:
        raise InvalidIdempotencyKeyError("must not be empty")
    max_length = get_setting("MAX_KEY_LENGTH")
    if len(key) > max_length:
        raise InvalidIdempotencyKeyError(f"must not exceed {max_length} characters")
    if not _KEY_PATTERN.match(key):
        raise InvalidIdempotencyKeyError(
            "must contain only letters, digits, and '-._~:' characters"
        )


def build_error_response(exc: IdempotencyError) -> JsonResponse:
    """Convert an :class:`~drf_idempotency.exceptions.IdempotencyError` to a response.

    This package's exceptions subclass
    :class:`rest_framework.exceptions.APIException` so that raising them
    from *inside a DRF view* (as the ``@idempotent`` decorator does) is
    automatically converted to a proper response by DRF's own
    ``APIView.dispatch()``/``handle_exception``. Plain Django middleware
    has no equivalent machinery, though, so
    :class:`~drf_idempotency.middleware.IdempotencyMiddleware` calls this
    function explicitly to get the same result.

    Args:
        exc: The exception to convert.

    Returns:
        A :class:`~django.http.JsonResponse` with the exception's
        ``status_code`` and a ``{"detail": ...}`` body.
    """
    return JsonResponse({"detail": str(exc.detail)}, status=exc.status_code)


def applies_to(request: HttpRequest) -> bool:
    """Return whether idempotency handling applies to this request's method.

    Args:
        request: The incoming request.

    Returns:
        ``True`` if ``request.method`` is in the configured ``METHODS``
        setting.
    """
    return request.method in get_setting("METHODS")


def process_idempotent_request(
    request: HttpRequest, call_view: Callable[[], HttpResponse]
) -> HttpResponse:
    """Apply idempotency-key handling around a view call.

    Args:
        request: The incoming request.
        call_view: A zero-argument callable that executes the real view
            and returns its response. Called at most once.

    Returns:
        Either a freshly-produced response (with idempotency headers
        added), or a byte-for-byte replayed response from a prior
        identical request.

    Raises:
        drf_idempotency.exceptions.MissingIdempotencyKeyError: If
            ``REQUIRE_KEY`` is enabled and no key header was supplied.
        drf_idempotency.exceptions.InvalidIdempotencyKeyError: If the
            supplied key fails validation.
        drf_idempotency.exceptions.IdempotencyKeyReuseError: If the key
            was previously used with a different request body.
        drf_idempotency.exceptions.ConcurrentRequestError: If another
            request using the same key is currently being processed.

    Note:
        If both :class:`~drf_idempotency.middleware.IdempotencyMiddleware`
        and :func:`~drf_idempotency.decorators.idempotent` end up wrapping
        the same request (e.g. the middleware is installed project-wide
        *and* a view also carries the decorator), this function only
        performs its acquire-or-replay logic once per request — the
        second, nested call detects it via a marker set on ``request``
        and simply calls ``call_view()`` directly. Without this, the
        inner call would try to acquire a lock the outer call already
        holds and fail with a spurious :class:`~drf_idempotency.exceptions.ConcurrentRequestError`.
    """
    if getattr(request, "_drf_idempotency_handled", False):
        return call_view()

    header_name = get_setting("HEADER_NAME")
    key = request.headers.get(header_name)
    if key is None:
        if get_setting("REQUIRE_KEY"):
            raise MissingIdempotencyKeyError
        return call_view()

    request._drf_idempotency_handled = True  # type: ignore[attr-defined]
    validate_key(key)
    fingerprint = compute_fingerprint(request)
    backend = get_backend()
    lock_ttl = timedelta(seconds=get_setting("LOCK_TTL_SECONDS"))

    result = backend.acquire_or_get(key, fingerprint, lock_ttl=lock_ttl)
    if not result.acquired:
        existing = result.existing
        if existing is None:  # pragma: no cover - guaranteed by the backend contract
            raise RuntimeError("Backend returned acquired=False with no existing record.")
        if existing.fingerprint != fingerprint:
            raise IdempotencyKeyReuseError(key)
        if existing.status != "completed":
            raise ConcurrentRequestError(key)
        return _build_replayed_response(
            existing,
            key=key,
            header_name=header_name,
            replay_header_name=get_setting("REPLAY_HEADER_NAME"),
        )

    try:
        response = call_view()
    except Exception:
        backend.fail(key)
        raise

    _finalize(response, backend=backend, key=key)
    response[header_name] = key
    response[get_setting("REPLAY_HEADER_NAME")] = "false"
    return response


def _finalize(request: HttpRequest | Request, response: HttpResponse, *, backend: BaseBackend, key: str) -> None:
    if isinstance(response, StreamingHttpResponse):
        # Streaming responses can't be captured for replay; release the
        # lock so a retry executes the view again rather than being stuck.
        backend.fail(key)
        return

    render = getattr(response, "render", None)
    if callable(render) and not getattr(response, "is_rendered", True):
        if isinstance(request, Request):
            # DRF needs more preparation for render.
            response.accepted_renderer = request.accepted_renderer
            response.accepted_media_type = request.accepted_media_type
            view = request.parser_context.get('view')
            response.renderer_context = view.get_renderer_context() if view else {}

        render()

    should_cache = response.status_code < 500 and (
        response.status_code < 400 or get_setting("CACHE_CLIENT_ERROR_RESPONSES")
    )
    if should_cache:
        backend.complete(
            key,
            status_code=response.status_code,
            headers=_extract_headers(response),
            body=response.content,
            ttl=timedelta(seconds=get_setting("TTL_SECONDS")),
        )
    else:
        backend.fail(key)


def _extract_headers(response: HttpResponse) -> dict[str, str]:
    return {
        name: value
        for name, value in response.items()
        if name.lower() not in _EXCLUDED_RESPONSE_HEADERS
    }


def _build_replayed_response(
    existing: StoredRecord, *, key: str, header_name: str, replay_header_name: str
) -> HttpResponse:
    response = HttpResponse(existing.response_body or b"", status=existing.response_status_code)
    for name, value in (existing.response_headers or {}).items():
        response[name] = value
    response[header_name] = key
    response[replay_header_name] = "true"
    return response
