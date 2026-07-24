"""Runtime dispatch: calling a registered tool with real DRF machinery.

:func:`execute_tool` takes a tool name and an arguments dict — exactly what
an LLM function/tool call produces — and dispatches it through the real
registered viewset using :meth:`~rest_framework.viewsets.ViewSetMixin.as_view`,
so authentication, permission checks, and serializer validation all run
exactly as they would for a genuine HTTP request. Nothing about request
dispatch is reimplemented; this module only translates between "tool call
arguments" and "DRF test request" shapes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate

from drf_llm_gateway.exceptions import (
    ToolNotFoundError,
    ToolPermissionDeniedError,
    ToolValidationError,
)
from drf_llm_gateway.registry import ToolDefinition, ToolRegistry, default_registry
from drf_llm_gateway.settings import get_setting

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
    from rest_framework.viewsets import ViewSetMixin

_factory = APIRequestFactory()


@dataclass(frozen=True, slots=True)
class ToolResult:
    """The outcome of successfully executing a tool.

    Attributes:
        status_code: The HTTP status code the underlying view produced.
        data: The response body as plain Python data (what
            ``response.data`` contained before rendering) — safe to
            ``json.dumps`` directly.
    """

    status_code: int
    data: Any


def execute_tool(
    name: str,
    arguments: dict[str, Any],
    *,
    user: AbstractBaseUser | AnonymousUser | None = None,
    registry: ToolRegistry | None = None,
) -> ToolResult:
    """Execute a registered tool with the given arguments.

    Args:
        name: The tool name, as produced by
            :func:`drf_llm_gateway.registry.expose_as_tool`.
        arguments: The tool call arguments. For detail actions, must
            include the key named by the tool's ``lookup_field``. For
            ``create``/``update``/``partial_update``, the remaining keys
            are validated against the tool's serializer exactly as a real
            request body would be.
        user: The identity to dispatch as. Defaults to
            :class:`~django.contrib.auth.models.AnonymousUser` — pass a
            real user instance to exercise permission classes that require
            authentication.
        registry: The registry to look ``name`` up in. Defaults to
            :data:`drf_llm_gateway.registry.default_registry`.

    Returns:
        A :class:`ToolResult` with the response status code and body.

    Raises:
        drf_llm_gateway.exceptions.ToolNotFoundError: If ``name`` isn't
            registered.
        drf_llm_gateway.exceptions.ToolValidationError: If the underlying
            view returned ``400 Bad Request`` (typically a serializer
            validation failure).
        drf_llm_gateway.exceptions.ToolPermissionDeniedError: If the
            underlying view returned ``401`` or ``403``.
    """
    source = registry if registry is not None else default_registry
    tool = source.get(name)
    if tool is None:
        raise ToolNotFoundError(name)
    if tool.detail and tool.lookup_field not in arguments:
        raise ToolValidationError({tool.lookup_field: ["This field is required."]})

    response = _dispatch(tool, arguments, user=user)
    if response.status_code in (401, 403):
        raise ToolPermissionDeniedError(name)
    if response.status_code == 400:
        raise ToolValidationError(response.data)
    return ToolResult(status_code=response.status_code, data=response.data)


def _dispatch(
    tool: ToolDefinition,
    arguments: dict[str, Any],
    *,
    user: AbstractBaseUser | AnonymousUser | None,
) -> Response:
    body = {k: v for k, v in arguments.items() if k != tool.lookup_field}
    method = tool.http_method.lower()
    factory_call = getattr(_factory, method)
    if method in ("post", "put", "patch"):
        django_request = factory_call("/", data=body, format="json")
    else:
        django_request = factory_call("/")

    force_authenticate(django_request, user=user)

    kwargs: dict[str, Any] = {}
    if tool.detail:
        kwargs[tool.lookup_field] = arguments[tool.lookup_field]

    viewset_class: type = tool.viewset_class
    if not get_setting("ENFORCE_PERMISSIONS"):
        viewset_class = type(viewset_class.__name__, (viewset_class,), {"permission_classes": []})

    view_callable = cast("type[ViewSetMixin]", viewset_class).as_view({method: tool.action})
    response = view_callable(django_request, **kwargs)
    if not response.is_rendered:
        response.render()
    return response
