"""Modern async support for Django REST Framework.

DRF's own ``APIView.dispatch()`` calls the resolved handler method
synchronously - an ``async def get(self, request)`` on a plain
``APIView`` returns an unawaited coroutine as the "response" and breaks
immediately. This package provides an async-native
:class:`~drf_async.views.AsyncAPIView` (and
:class:`~drf_async.generics.AsyncGenericAPIView`,
:class:`~drf_async.viewsets.AsyncModelViewSet`, and the individual
async mixins) whose ``dispatch()`` is a real coroutine throughout,
correctly bridging DRF's synchronous permission/throttle/serializer
internals via a thread where they might touch the database, while
letting your own handler code use Django's async ORM directly.

The public API is intentionally structured to mirror
``rest_framework.views``/``generics``/``mixins``/``viewsets`` one-to-one
- if you know DRF, you already know this package.
"""

from __future__ import annotations

from drf_async.generics import (
    AsyncCreateAPIView,
    AsyncDestroyAPIView,
    AsyncGenericAPIView,
    AsyncListAPIView,
    AsyncListCreateAPIView,
    AsyncRetrieveAPIView,
    AsyncRetrieveDestroyAPIView,
    AsyncRetrieveUpdateAPIView,
    AsyncRetrieveUpdateDestroyAPIView,
    AsyncUpdateAPIView,
)
from drf_async.mixins import (
    AsyncCreateModelMixin,
    AsyncDestroyModelMixin,
    AsyncListModelMixin,
    AsyncRetrieveModelMixin,
    AsyncUpdateModelMixin,
)
from drf_async.permissions import BaseAsyncPermission
from drf_async.throttling import (
    AsyncAnonRateThrottle,
    AsyncSimpleRateThrottle,
    AsyncUserRateThrottle,
    BaseAsyncThrottle,
)
from drf_async.views import AsyncAPIView
from drf_async.viewsets import (
    AsyncGenericViewSet,
    AsyncModelViewSet,
    AsyncReadOnlyModelViewSet,
)

__version__ = "1.0.0"

__all__ = [
    "AsyncAPIView",
    "AsyncAnonRateThrottle",
    "AsyncCreateAPIView",
    "AsyncCreateModelMixin",
    "AsyncDestroyAPIView",
    "AsyncDestroyModelMixin",
    "AsyncGenericAPIView",
    "AsyncGenericViewSet",
    "AsyncListAPIView",
    "AsyncListCreateAPIView",
    "AsyncListModelMixin",
    "AsyncModelViewSet",
    "AsyncReadOnlyModelViewSet",
    "AsyncRetrieveAPIView",
    "AsyncRetrieveDestroyAPIView",
    "AsyncRetrieveModelMixin",
    "AsyncRetrieveUpdateAPIView",
    "AsyncRetrieveUpdateDestroyAPIView",
    "AsyncSimpleRateThrottle",
    "AsyncUpdateAPIView",
    "AsyncUpdateModelMixin",
    "AsyncUserRateThrottle",
    "BaseAsyncPermission",
    "BaseAsyncThrottle",
    "__version__",
]
