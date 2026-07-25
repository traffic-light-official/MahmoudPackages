"""A view mixin that adds Deprecation/Sunset/Link response headers.

Deliberately implemented as a view-level mixin (overriding
``finalize_response``), not a Django middleware: DRF sets
``request.version`` on its own ``Request`` wrapper instance inside
``APIView.dispatch()``, which a plain Django middleware's captured
``HttpRequest`` reference never sees - see ``docs/architecture.md``.
"""

from __future__ import annotations

import datetime
from email.utils import format_datetime
from typing import TYPE_CHECKING, Any

from drf_api_versioning import registry
from drf_api_versioning.settings import get_setting

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.response import Response


class DeprecationHeaderMixin:
    """Adds ``Deprecation``/``Sunset``/``Link`` headers for a deprecated version.

    Add to any ``APIView``/``ViewSet`` using a registry-aware versioning
    scheme from :mod:`drf_api_versioning.versioning`:

    .. code-block:: python

        class ArticleViewSet(DeprecationHeaderMixin, viewsets.ModelViewSet):
            versioning_class = URLPathVersioning
    """

    def finalize_response(
        self, request: Request, response: Response, *args: Any, **kwargs: Any
    ) -> Response:
        """Call ``super()`` first, then add headers if the version is deprecated."""
        response = super().finalize_response(  # type: ignore[misc]
            request, response, *args, **kwargs
        )
        version = getattr(request, "version", None)
        if version is None:
            return response

        info = registry.get_version_info(version)
        if info.deprecated_on is not None and info.is_deprecated():
            response[get_setting("DEPRECATION_HEADER")] = _format_http_date(info.deprecated_on)
        if info.sunset_on is not None:
            response[get_setting("SUNSET_HEADER")] = _format_http_date(info.sunset_on)
        if info.deprecation_link and (info.is_deprecated() or info.is_sunset()):
            response[get_setting("LINK_HEADER")] = f'<{info.deprecation_link}>; rel="deprecation"'
        return response


def _format_http_date(value: datetime.date) -> str:
    """Format a date as an RFC 7231 HTTP-date, at midnight UTC."""
    as_datetime = datetime.datetime.combine(value, datetime.time.min, tzinfo=datetime.timezone.utc)
    return format_datetime(as_datetime, usegmt=True)
