"""Async equivalents of ``rest_framework.mixins``.

Each mixin's action method (``list``/``create``/``retrieve``/
``update``/``partial_update``/``destroy``) is named **identically** to
its synchronous DRF counterpart, just defined as ``async def`` -
deliberately, not ``alist``/``acreate``/etc. DRF's routers
(``SimpleRouter``/``DefaultRouter``) hardcode these exact action name
strings and bind them via ``getattr(self, action)`` inside
``ViewSetMixin.as_view()``; a differently-named method would never be
found, breaking routing outright rather than just working
sub-optimally. See ``docs/architecture.md`` for the full explanation.

Internal helper methods this package introduces itself (not
router-bound action names) keep the conventional ``a``-prefix, matching
Django's own async ORM naming (``aget_object``, ``aperform_create``,
etc.) - only the *action* methods must match DRF's naming exactly.

Queryset evaluation uses the async ORM (``async for``, ``.aget()``,
``.adelete()``) directly. ``serializer.is_valid()``/``.save()`` (which
may run database-touching validators, and does run the model's own
``save()``/``delete()``) are bridged through a thread via
``sync_to_async`` - see the module docstring in :mod:`drf_async.compat`
for why. If you need genuinely async-native create/update (using
``Model.objects.acreate()`` directly instead of bridging
``serializer.save()``), override ``aperform_create``/``aperform_update``
yourself - see ``docs/advanced-usage.md``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from asgiref.sync import sync_to_async
from rest_framework import status
from rest_framework.response import Response
from rest_framework.settings import api_settings

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.serializers import BaseSerializer


class AsyncListModelMixin:
    """Async equivalent of ``rest_framework.mixins.ListModelMixin``."""

    async def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """List every object in the (filtered, paginated) queryset."""
        queryset = self.filter_queryset(self.get_queryset())  # type: ignore[attr-defined]

        page = await self.apaginate_queryset(queryset)  # type: ignore[attr-defined]
        if page is not None:
            serializer = self.get_serializer(page, many=True)  # type: ignore[attr-defined]
            return self.get_paginated_response(serializer.data)  # type: ignore[attr-defined,no-any-return]

        objects = [obj async for obj in queryset]
        serializer = self.get_serializer(objects, many=True)  # type: ignore[attr-defined]
        return Response(serializer.data)


class AsyncCreateModelMixin:
    """Async equivalent of ``rest_framework.mixins.CreateModelMixin``."""

    async def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Validate and save a new object."""
        serializer = self.get_serializer(data=request.data)  # type: ignore[attr-defined]
        await sync_to_async(serializer.is_valid, thread_sensitive=True)(raise_exception=True)
        await self.aperform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    async def aperform_create(self, serializer: BaseSerializer[Any]) -> None:
        """Save the validated serializer. Override for a genuinely async ``create()``."""
        await sync_to_async(serializer.save, thread_sensitive=True)()

    def get_success_headers(self, data: dict[str, Any]) -> dict[str, str]:
        """Return a ``Location`` header pointing at the new object, if it has a URL."""
        try:
            return {"Location": str(data[api_settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            return {}


class AsyncRetrieveModelMixin:
    """Async equivalent of ``rest_framework.mixins.RetrieveModelMixin``."""

    async def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Return a single object, looked up by the URL's lookup kwarg."""
        instance = await self.aget_object()  # type: ignore[attr-defined]
        serializer = self.get_serializer(instance)  # type: ignore[attr-defined]
        return Response(serializer.data)


class AsyncUpdateModelMixin:
    """Async equivalent of ``rest_framework.mixins.UpdateModelMixin``."""

    async def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Validate and save changes to an existing object (full update)."""
        partial = kwargs.pop("partial", False)
        instance = await self.aget_object()  # type: ignore[attr-defined]
        serializer = self.get_serializer(instance, data=request.data, partial=partial)  # type: ignore[attr-defined]
        await sync_to_async(serializer.is_valid, thread_sensitive=True)(raise_exception=True)
        await self.aperform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    async def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """``update`` with ``partial=True``."""
        kwargs["partial"] = True
        return await self.update(request, *args, **kwargs)

    async def aperform_update(self, serializer: BaseSerializer[Any]) -> None:
        """Save the validated serializer. Override for a genuinely async ``update()``."""
        await sync_to_async(serializer.save, thread_sensitive=True)()


class AsyncDestroyModelMixin:
    """Async equivalent of ``rest_framework.mixins.DestroyModelMixin``."""

    async def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delete an existing object."""
        instance = await self.aget_object()  # type: ignore[attr-defined]
        await self.aperform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    async def aperform_destroy(self, instance: Any) -> None:
        """Delete the instance, using Django's async ``Model.adelete()``."""
        await instance.adelete()
