"""``AsyncAPIView``: an async-native replacement for ``rest_framework.views.APIView``.

DRF's own ``APIView.dispatch()`` calls the resolved handler method
synchronously (``response = handler(request, *args, **kwargs)``) - if
that handler were ``async def``, this would assign an unawaited
coroutine as the response and break immediately. ``AsyncAPIView``
overrides ``dispatch()`` (and everything ``initial()`` calls that might
touch the database) to be ``async def`` throughout, so handler methods
can be real coroutines using Django's async ORM directly.

Everything unrelated to the request/response lifecycle itself
(content negotiation, exception-to-response conversion, parser/renderer
selection) is untouched DRF code, called synchronously, since none of
it does I/O.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from asgiref.sync import sync_to_async
from rest_framework.views import APIView

from drf_async.permissions import check_object_permission, check_permission
from drf_async.throttling import check_throttle, wait_for_throttle

if TYPE_CHECKING:
    from django.http import HttpRequest
    from rest_framework.request import Request
    from rest_framework.response import Response


class AsyncAPIView(APIView):
    """An async-native ``APIView``. Define handler methods as ``async def``.

    .. code-block:: python

        class PingView(AsyncAPIView):
            async def get(self, request, *args, **kwargs):
                return Response({"pong": True})

    Permission and throttle classes may be either classic synchronous
    ones (bridged automatically via a thread) or async-native ones from
    :mod:`drf_async.permissions`/:mod:`drf_async.throttling` (awaited
    directly) - mix and match freely.
    """

    async def dispatch(  # type: ignore[override]
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> Response:
        """Async equivalent of ``APIView.dispatch()`` - see the module docstring."""
        self.args = args
        self.kwargs = kwargs
        drf_request = self.initialize_request(request, *args, **kwargs)
        self.request = drf_request
        self.headers = self.default_response_headers

        try:
            await self.ainitial(drf_request, *args, **kwargs)

            if (
                drf_request.method is not None
                and drf_request.method.lower() in self.http_method_names
            ):
                handler = getattr(self, drf_request.method.lower(), self.ahttp_method_not_allowed)
            else:
                handler = self.ahttp_method_not_allowed

            response = await handler(drf_request, *args, **kwargs)
        except Exception as exc:
            response = self.handle_exception(exc)

        self.response = self.finalize_response(drf_request, response, *args, **kwargs)
        return self.response

    async def ahttp_method_not_allowed(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Response:
        """Async equivalent of ``APIView.http_method_not_allowed``."""
        return self.http_method_not_allowed(request, *args, **kwargs)

    async def ainitial(self, request: Request, *args: Any, **kwargs: Any) -> None:
        """Async equivalent of ``APIView.initial()``."""
        self.format_kwarg = self.get_format_suffix(**kwargs)

        neg = self.perform_content_negotiation(request)
        request.accepted_renderer, request.accepted_media_type = neg

        version, scheme = self.determine_version(request, *args, **kwargs)
        request.version, request.versioning_scheme = version, scheme

        await self.aperform_authentication(request)
        await self.acheck_permissions(request)
        await self.acheck_throttles(request)

    async def aperform_authentication(self, request: Request) -> None:
        """Async equivalent of ``APIView.perform_authentication()``.

        Accessing ``request.user`` triggers DRF's lazy authentication,
        which runs each configured authenticator's (synchronous, often
        database-touching) ``authenticate()`` - bridged via a thread.
        """
        await sync_to_async(lambda: request.user, thread_sensitive=True)()

    async def acheck_permissions(self, request: Request) -> None:
        """Async equivalent of ``APIView.check_permissions()``."""
        for permission in self.get_permissions():
            if not await check_permission(permission, request, self):
                self.permission_denied(
                    request,
                    message=getattr(permission, "message", None),
                    code=getattr(permission, "code", None),
                )

    async def acheck_object_permissions(self, request: Request, obj: Any) -> None:
        """Async equivalent of ``APIView.check_object_permissions()``."""
        for permission in self.get_permissions():
            if not await check_object_permission(permission, request, self, obj):
                self.permission_denied(
                    request,
                    message=getattr(permission, "message", None),
                    code=getattr(permission, "code", None),
                )

    async def acheck_throttles(self, request: Request) -> None:
        """Async equivalent of ``APIView.check_throttles()``."""
        throttle_durations = []
        for throttle in self.get_throttles():
            if not await check_throttle(throttle, request, self):
                throttle_durations.append(await wait_for_throttle(throttle))

        if throttle_durations:
            durations = [duration for duration in throttle_durations if duration is not None]
            duration = max(durations, default=None)
            # DRF's own real APIView.check_throttles() passes a possibly-None
            # duration here too - the stub's `wait: float` is imprecise.
            self.throttled(request, duration)  # type: ignore[arg-type]
