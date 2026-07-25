"""``AsyncGenericAPIView``: adds async object/pagination support to ``AsyncAPIView``.

``django.shortcuts.aget_object_or_404`` does not exist at this
package's minimum supported Django version (4.2 - it was added in
5.0), so :meth:`AsyncGenericAPIView.aget_object` implements the
equivalent directly: ``queryset.aget(**filter_kwargs)``, translating
``DoesNotExist``/a malformed lookup value into ``Http404``, the same
outcomes DRF's own (synchronous) ``get_object_or_404`` produces.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from asgiref.sync import sync_to_async
from django.core.exceptions import ValidationError
from django.http import Http404
from rest_framework.exceptions import APIException
from rest_framework.generics import GenericAPIView

from drf_async.mixins import (
    AsyncCreateModelMixin,
    AsyncDestroyModelMixin,
    AsyncListModelMixin,
    AsyncRetrieveModelMixin,
    AsyncUpdateModelMixin,
)
from drf_async.views import AsyncAPIView

if TYPE_CHECKING:
    from django.db.models import Model, QuerySet
    from rest_framework.request import Request
    from rest_framework.response import Response


class AsyncGenericAPIView(AsyncAPIView, GenericAPIView[Any]):
    """``GenericAPIView`` with an async ``aget_object``/``apaginate_queryset``.

    Parametrized ``GenericAPIView[Any]`` rather than a concrete model,
    matching DRF's own ``generics.py``: this is a reusable base class,
    not tied to one model, the same way DRF's own is - a project using
    this class for a specific model is free to parametrize its own
    concrete subclass further if it wants stricter typing.

    Everything else (``get_queryset``, ``get_serializer``,
    ``filter_queryset``, ``get_paginated_response``) is unchanged,
    synchronous DRF code - none of it does I/O by itself; only
    evaluating a queryset (a slice, ``.aget()``, ``list()``, ``.count()``)
    actually touches the database.
    """

    async def aget_object(self) -> Model:
        """Async equivalent of ``GenericAPIView.get_object()``."""
        queryset: QuerySet[Any] = self.filter_queryset(self.get_queryset())

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        if lookup_url_kwarg not in self.kwargs:
            raise AssertionError(
                f"Expected view {self.__class__.__name__} to be called with a URL "
                f'keyword argument named "{lookup_url_kwarg}". Fix your URL conf, or set '
                "the `.lookup_field` attribute on the view correctly."
            )
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}

        try:
            obj = await queryset.aget(**filter_kwargs)
        except (TypeError, ValueError, ValidationError) as exc:
            raise Http404 from exc
        except queryset.model.DoesNotExist as exc:
            raise Http404 from exc

        await self.acheck_object_permissions(self.request, obj)
        return obj  # type: ignore[no-any-return]

    async def apaginate_queryset(self, queryset: QuerySet[Any]) -> list[Any] | None:
        """Async equivalent of ``GenericAPIView.paginate_queryset()``.

        Bridges the (synchronous, but I/O-free-until-evaluated) paginator
        through a thread rather than reimplementing pagination - DRF's
        pagination classes are reused entirely unchanged.
        """
        if self.paginator is None:
            return None
        return await sync_to_async(self.paginator.paginate_queryset, thread_sensitive=True)(
            queryset, self.request, view=self
        )

    def get_paginated_response(self, data: Any) -> Response:
        """Return a paginated ``Response`` - identical to the sync version."""
        if self.paginator is None:
            raise APIException("Cannot paginate: no `pagination_class` is configured.")
        return self.paginator.get_paginated_response(data)


# Concrete view classes, composing the mixins above with AsyncGenericAPIView -
# mirroring rest_framework.generics's own ListAPIView/CreateAPIView/etc.,
# one HTTP-verb method per class delegating to the matching mixin action.


class AsyncCreateAPIView(AsyncCreateModelMixin, AsyncGenericAPIView):
    """Concrete view for creating a model instance."""

    async def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delegate to :meth:`~drf_async.mixins.AsyncCreateModelMixin.create`."""
        return await self.create(request, *args, **kwargs)


class AsyncListAPIView(AsyncListModelMixin, AsyncGenericAPIView):
    """Concrete view for listing a queryset."""

    async def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delegate to :meth:`~drf_async.mixins.AsyncListModelMixin.list`."""
        return await self.list(request, *args, **kwargs)


class AsyncRetrieveAPIView(AsyncRetrieveModelMixin, AsyncGenericAPIView):
    """Concrete view for retrieving a model instance."""

    async def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delegate to :meth:`~drf_async.mixins.AsyncRetrieveModelMixin.retrieve`."""
        return await self.retrieve(request, *args, **kwargs)


class AsyncDestroyAPIView(AsyncDestroyModelMixin, AsyncGenericAPIView):
    """Concrete view for deleting a model instance."""

    async def delete(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delegate to :meth:`~drf_async.mixins.AsyncDestroyModelMixin.destroy`."""
        return await self.destroy(request, *args, **kwargs)


class AsyncUpdateAPIView(AsyncUpdateModelMixin, AsyncGenericAPIView):
    """Concrete view for updating a model instance."""

    async def put(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delegate to :meth:`~drf_async.mixins.AsyncUpdateModelMixin.update`."""
        return await self.update(request, *args, **kwargs)

    async def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delegate to :meth:`~drf_async.mixins.AsyncUpdateModelMixin.partial_update`."""
        return await self.partial_update(request, *args, **kwargs)


class AsyncListCreateAPIView(AsyncListModelMixin, AsyncCreateModelMixin, AsyncGenericAPIView):
    """Concrete view for listing a queryset or creating a model instance."""

    async def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delegate to :meth:`~drf_async.mixins.AsyncListModelMixin.list`."""
        return await self.list(request, *args, **kwargs)

    async def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delegate to :meth:`~drf_async.mixins.AsyncCreateModelMixin.create`."""
        return await self.create(request, *args, **kwargs)


class AsyncRetrieveUpdateAPIView(
    AsyncRetrieveModelMixin, AsyncUpdateModelMixin, AsyncGenericAPIView
):
    """Concrete view for retrieving or updating a model instance."""

    async def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delegate to :meth:`~drf_async.mixins.AsyncRetrieveModelMixin.retrieve`."""
        return await self.retrieve(request, *args, **kwargs)

    async def put(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delegate to :meth:`~drf_async.mixins.AsyncUpdateModelMixin.update`."""
        return await self.update(request, *args, **kwargs)

    async def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delegate to :meth:`~drf_async.mixins.AsyncUpdateModelMixin.partial_update`."""
        return await self.partial_update(request, *args, **kwargs)


class AsyncRetrieveDestroyAPIView(
    AsyncRetrieveModelMixin, AsyncDestroyModelMixin, AsyncGenericAPIView
):
    """Concrete view for retrieving or deleting a model instance."""

    async def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delegate to :meth:`~drf_async.mixins.AsyncRetrieveModelMixin.retrieve`."""
        return await self.retrieve(request, *args, **kwargs)

    async def delete(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delegate to :meth:`~drf_async.mixins.AsyncDestroyModelMixin.destroy`."""
        return await self.destroy(request, *args, **kwargs)


class AsyncRetrieveUpdateDestroyAPIView(
    AsyncRetrieveModelMixin, AsyncUpdateModelMixin, AsyncDestroyModelMixin, AsyncGenericAPIView
):
    """Concrete view for retrieving, updating, or deleting a model instance."""

    async def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delegate to :meth:`~drf_async.mixins.AsyncRetrieveModelMixin.retrieve`."""
        return await self.retrieve(request, *args, **kwargs)

    async def put(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delegate to :meth:`~drf_async.mixins.AsyncUpdateModelMixin.update`."""
        return await self.update(request, *args, **kwargs)

    async def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delegate to :meth:`~drf_async.mixins.AsyncUpdateModelMixin.partial_update`."""
        return await self.partial_update(request, *args, **kwargs)

    async def delete(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delegate to :meth:`~drf_async.mixins.AsyncDestroyModelMixin.destroy`."""
        return await self.destroy(request, *args, **kwargs)
